(in-package :expert/engine)

(defparameter *field-weights*
  '(("жанр" . 10)
    ("эпоха" . 2)
    ("настроение" . 2)
    ("темы" . 2)
    ("сложность" . 1)
    ("объём" . 1)))

(defparameter *field-salience*
  '(("жанр" . 333)
    ("эпоха" . 60)
    ("настроение" . 60)
    ("темы" . 55)
    ("сложность" . 50)
    ("объём" . 50)))

(defparameter *rules* '())

(defstruct es-rule
  name
  type
  salience
  book-id
  book-title
  field
  value
  weight
  description)

(defun field-weight (field)
  (or (cdr (assoc field *field-weights* :test #'equal)) 1))

(defun field-salience (field)
  (or (cdr (assoc field *field-salience* :test #'equal)) 50))

(defun format-init-description (book-title)
  (format nil "Если система запускается, То создать кандидата для книги '~a' с начальным счётом 0"
          book-title))

(defun format-match-description (book-title field value weight)
  (format nil "Если пользователь выбрал ~a='~a' И книга '~a' имеет ~a='~a', То увеличить счёт книги на ~d очко(а/ов)"
          field (expert/frames:human-label field value)
          book-title field (expert/frames:human-label field value)
          weight))

(defun build-rules ()
  (setf *rules* '())
  (dolist (book *books*)
    (let ((book-id (getf book :id))
          (title (getf book :title)))
      (push (make-es-rule
             :name (format nil "init__~a" title)
             :type :initialization
             :salience 100
             :book-id book-id
             :book-title title
             :description (format-init-description title))
            *rules*)))
  (let ((seen (make-hash-table :test #'equal)))
    (dolist (book *books*)
      (let ((book-id (getf book :id))
            (title (getf book :title)))
        (dolist (entry (getf book :match))
          (let ((field (car entry))
                (raw-val (cdr entry)))
            (dolist (value (if (listp raw-val) raw-val (list raw-val)))
              (let ((key (list title field value)))
                (unless (gethash key seen)
                  (setf (gethash key seen) t)
                  (let ((weight (field-weight field)))
                    (push
                     (make-es-rule
                      :name (format nil "match__~a__~a__~a" title field value)
                      :type :matching
                      :salience (field-salience field)
                      :book-id book-id
                      :book-title title
                      :field field
                      :value value
                      :weight weight
                      :description (format-match-description title field value weight))
                     *rules*))))))))))
  (setf *rules* (sort *rules* (lambda (a b)
                                 (> (es-rule-salience a) (es-rule-salience b)))))
  (length *rules*))

(defun pref-key (field value)
  (list :pref field value))

(defun candidate-key (book-id)
  (list :candidate book-id))

(defun processed-key (book-id field value)
  (list :processed book-id field value))

(defun make-working-memory ()
  (make-hash-table :test #'equal))

(defun wm-get-candidate (wm book-id)
  (gethash (candidate-key book-id) wm))

(defun wm-has-pref (wm field value)
  (gethash (pref-key field value) wm))

(defun wm-has-processed (wm book-id field value)
  (gethash (processed-key book-id field value) wm))

(defun wm-set-candidate (wm book-id title score matched)
  (setf (gethash (candidate-key book-id) wm)
        (list :book-id book-id :title title :score score :matched matched)))

(defun human-match (field value)
  (format nil "~a=~a" field (expert/frames:human-label field value)))

(defun fire-init-rule (wm rule)
  (let ((book-id (es-rule-book-id rule))
        (title (es-rule-book-title rule)))
    (unless (wm-get-candidate wm book-id)
      (wm-set-candidate wm book-id title 0 '())
      t)))

(defun fire-match-rule (wm rule)
  (let* ((field (es-rule-field rule))
         (value (es-rule-value rule))
         (book-id (es-rule-book-id rule))
         (candidate (wm-get-candidate wm book-id)))
    (when (and candidate
               (wm-has-pref wm field value)
               (not (wm-has-processed wm book-id field value)))
      (let* ((score (getf candidate :score))
             (matched (getf candidate :matched))
             (label (human-match field value)))
        (wm-set-candidate wm book-id (getf candidate :title)
                          (+ score (es-rule-weight rule))
                          (if (member label matched :test #'equal)
                              matched
                              (append matched (list label))))
        (setf (gethash (processed-key book-id field value) wm) t)
        t))))

(defun run-forward-chaining (prefs)
  (let ((wm (make-working-memory)))
    (dolist (rule *rules*)
      (when (eq (es-rule-type rule) :initialization)
        (fire-init-rule wm rule)))
    (dolist (pref prefs)
      (setf (gethash (pref-key (car pref) (cdr pref)) wm) t))
    (loop for changed = nil
          do (setf changed nil)
             (dolist (rule *rules*)
               (when (eq (es-rule-type rule) :matching)
                 (when (fire-match-rule wm rule)
                   (setf changed t))))
          while changed)
    wm))

(defun collect-recommendations (wm top-k)
  (let ((results '()))
    (maphash
     (lambda (_ candidate)
       (when (> (getf candidate :score) 0)
         (push candidate results)))
     wm)
    (setf results (sort results #'> :key (lambda (c) (getf c :score))))
    (loop for candidate in results
          for i from 0
          while (< i top-k)
          collect
          (let* ((title (getf candidate :title))
                 (book (find title *books* :key (lambda (b) (getf b :title)) :test #'equal)))
            (list :id (getf book :id)
                  :title title
                  :score (getf candidate :score)
                  :matched (sort (copy-list (getf candidate :matched)) #'string<)
                  :info (getf book :raw))))))

(defun get-recommendations (prefs &key (top-k 5))
  (collect-recommendations (run-forward-chaining prefs) top-k))

(defun get-all-recommendations ()
  (loop for book in *books*
        collect (list :id (getf book :id)
                      :title (getf book :title)
                      :score 0
                      :matched '()
                      :info (getf book :raw))))

(defun rule->plist (rule)
  (list :name (es-rule-name rule)
        :type (string-downcase (symbol-name (es-rule-type rule)))
        :salience (es-rule-salience rule)
        :description (es-rule-description rule)
        :book (es-rule-book-title rule)
        :field (es-rule-field rule)
        :value (es-rule-value rule)))

(defun get-rules-info (&key rule-type limit)
  (let ((init-count 0)
        (match-count 0)
        (filtered '()))
    (dolist (rule *rules*)
      (case (es-rule-type rule)
        (:initialization (incf init-count))
        (:matching (incf match-count)))
      (when (or (null rule-type)
                (string= rule-type "all")
                (and (string= rule-type "init") (eq (es-rule-type rule) :initialization))
                (and (string= rule-type "match") (eq (es-rule-type rule) :matching)))
        (push (rule->plist rule) filtered)))
    (setf filtered (reverse filtered))
    (when (and limit (> limit 0))
      (setf filtered (subseq filtered 0 (min limit (length filtered)))))
    (list :total_rules (+ init-count match-count)
          :init_rules_count init-count
          :match_rules_count match-count
          :other_rules_count 0
          :filtered_rules_count (length filtered)
          :rules filtered
          :statistics (list :total_books (length *books*)
                            :questions (length (expert/dialog:default-questions))
                            :average_rules_per_book
                            (if (plusp (length *books*))
                                (/ (+ init-count match-count) (length *books*))
                                0)))))
