(in-package :expert/dialog)

(defun default-questions ()
  '((:id "gq-1" :field "жанр" :prompt "Выберите жанр" :is-multi nil)
    (:id "gq-2" :field "эпоха" :prompt "Выберите эпоху" :is-multi nil)
    (:id "gq-3" :field "настроение" :prompt "Выберите настроение" :is-multi nil)
    (:id "gq-4" :field "сложность" :prompt "Выберите сложность" :is-multi nil)
    (:id "gq-5" :field "объём" :prompt "Выберите объём" :is-multi nil)
    (:id "gq-6" :field "темы" :prompt "Выберите одну или несколько тем" :is-multi t)))

(defun qget (question key)
  (getf question key))

(defun split-chars (s sep)
  (loop with start = 0
        for i from 0 to (length s)
        when (or (= i (length s)) (char= (char s i) sep))
          collect (subseq s start i)
          and do (setf start (1+ i))))

(defun hints-for (field &key (limit 16))
  (let ((vals (gethash field *options*)))
    (subseq (sort (copy-list vals) #'string<) 0 (min limit (length vals)))))

(defun parse-answers-payload (s)
  (when (and s (plusp (length s)))
    (loop for part in (split-chars s #\;)
          for pos = (position #\= part)
          when pos
            collect
            (let* ((value (subseq part (1+ pos)))
                   (items (split-chars value #\,)))
              (cons (subseq part 0 pos)
                    (if (> (length items) 1) items value))))))

(defun answers-to-prefs (payload)
  (let* ((answers (parse-answers-payload payload))
         (prefs '())
         (extra (copy-list answers)))
    (dolist (q (default-questions))
      (let* ((qid (qget q :id))
             (field (qget q :field))
             (options (gethash field *labels*))
             (pair (assoc qid answers :test #'string=)))
        (unless pair
          (error "Нет ответа на вопрос ~a (~a)" qid (qget q :prompt)))
        (setf extra (delete pair extra :test #'eq))
        (if (qget q :is-multi)
            (let ((items (if (listp (cdr pair)) (cdr pair) (list (cdr pair))))
                  (accepted 0)
                  (unknown '()))
              (dolist (item items)
                (let ((norm (string-normalize item)))
                  (if (gethash norm options)
                      (progn (push (cons field norm) prefs) (incf accepted))
                      (push item unknown))))
              (when (zerop accepted)
                (error "Неизвестные значения для ~a: ~{~a~^, ~}" field unknown)))
            (let ((norm (string-normalize (cdr pair))))
              (unless (gethash norm options)
                (error "Неизвестное значение для ~a: ~a" field (cdr pair)))
              (push (cons field norm) prefs)))))
    (when extra
      (error "Неизвестные question_id: ~{~a~^, ~}" (mapcar #'car extra)))
    (nreverse prefs)))

(defun submit-answers (payload top-k)
  (format-recommendations
   (get-recommendations (answers-to-prefs payload) :top-k top-k)))

(defun format-recommendations (recs)
  (loop for rec in recs
        for info = (getf rec :info)
        collect
        (list :title (getf rec :title)
              :score (getf rec :score)
              :matched (getf rec :matched)
              :author (raw-get info "автор")
              :genre (raw-get info "жанр")
              :epoch (raw-get info "эпоха")
              :mood (raw-get info "настроение")
              :difficulty (raw-get info "сложность")
              :volume (raw-get info "объём")
              :image (raw-get info "изображение"))))
