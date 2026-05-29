(in-package :expert/engine)

;;; Веса полей — чем важнее критерий, тем больше очков за совпадение.
(defparameter *field-weights*
  '(("жанр" . 10)
    ("эпоха" . 2)
    ("настроение" . 2)
    ("темы" . 2)
    ("сложность" . 1)
    ("объём" . 1)))

(defun field-weight (field)
  (or (cdr (assoc field *field-weights* :test #'equal)) 1))

(defun book-values (book field)
  (let ((entry (assoc field (getf book :match) :test #'equal)))
    (when entry
      (let ((val (cdr entry)))
        (if (listp val) val (list val))))))

(defun match-label (field value)
  (format nil "~a=~a" field (human-label field value)))

(defun score-book (book prefs)
  (loop with score = 0
        with matched = '()
        for (field . value) in prefs
        for book-values = (book-values book field)
        when (and book-values (member value book-values :test #'equal))
          do (incf score (field-weight field))
             (push (match-label field value) matched)
        finally (return (list :score score :matched (sort matched #'string<)))))

(defun book->recommendation (book score matched)
  (list :id (getf book :id)
        :title (getf book :title)
        :score score
        :matched matched
        :info (getf book :raw)))

(defun build-rules ()
  ;; Совместимость с init: правила не генерируем, логика — прямой подбор.
  (length *books*))

(defun get-recommendations (prefs &key (top-k 5))
  (let ((results
         (loop for book in *books*
               for scored = (score-book book prefs)
               for score = (getf scored :score)
               when (plusp score)
               collect (book->recommendation book score (getf scored :matched)))))
    (subseq (sort results #'> :key (lambda (r) (getf r :score)))
            0 (min top-k (length results)))))

(defun get-all-recommendations ()
  (loop for book in *books*
        collect (book->recommendation book 0 '())))

(defun get-rules-info (&key rule-type limit)
  (declare (ignore rule-type limit))
  (list :total_rules 0
        :init_rules_count 0
        :match_rules_count 0
        :rules '()))
