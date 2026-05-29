(in-package :expert/dialog)

(defparameter *sessions* (make-hash-table :test 'equal))
(defparameter *session-counter* 0)

(defstruct dialog-session
  id
  idx
  prefs
  answer-counts)

(defun default-questions ()
  '((:id "gq-1" :field "жанр" :prompt "Выберите жанр" :is-multi nil)
    (:id "gq-2" :field "эпоха" :prompt "Выберите эпоху" :is-multi nil)
    (:id "gq-3" :field "настроение" :prompt "Выберите настроение" :is-multi nil)
    (:id "gq-4" :field "сложность" :prompt "Выберите сложность" :is-multi nil)
    (:id "gq-5" :field "объём" :prompt "Выберите объём" :is-multi nil)
    (:id "gq-6" :field "темы" :prompt "Выберите одну или несколько тем" :is-multi t)))

(defun qget (question key)
  (getf question key))

(defun new-session ()
  (incf *session-counter*)
  (let ((id (format nil "session-~d" *session-counter*)))
    (let ((session (make-dialog-session
                    :id id
                    :idx 0
                    :prefs '()
                    :answer-counts '())))
      (setf (gethash id *sessions*) session)
      id)))

(defun get-session (session-id)
  (or (gethash session-id *sessions*)
      (error "Unknown session: ~a" session-id)))

(defun session-is-done (session-id)
  (>= (dialog-session-idx (get-session session-id))
      (length (default-questions))))

(defun session-can-go-back (session-id)
  (> (dialog-session-idx (get-session session-id)) 0))

(defun session-prefs (session-id)
  (dialog-session-prefs (get-session session-id)))

(defun session-go-back (session-id)
  (let ((session (get-session session-id)))
    (unless (session-can-go-back session-id)
      (error "Невозможно вернуться назад. Вы на первом вопросе."))
    (decf (dialog-session-idx session))
    (let ((count (pop (dialog-session-answer-counts session))))
      (dotimes (_ count)
        (pop (dialog-session-prefs session)))
      t)))

(defun hints-for (field &key (limit 16))
  (let ((vals (gethash field *options*)))
    (subseq (sort (copy-list vals) #'string<) 0 (min limit (length vals)))))

(defun session-question (session-id)
  (let* ((session (get-session session-id))
         (questions (default-questions)))
    (when (>= (dialog-session-idx session) (length questions))
      (return-from session-question nil))
    (let* ((q (nth (dialog-session-idx session) questions))
           (field (qget q :field)))
      (list :type "question"
            :question_id (qget q :id)
            :field field
            :text (qget q :prompt)
            :avaliable_answers (hints-for field)
            :is_multiple_response_options (qget q :is-multi)))))

(defun session-add-answer (session-id &key text-answer items-answer)
  (let* ((session (get-session session-id))
         (questions (default-questions)))
    (when (>= (dialog-session-idx session) (length questions))
      (error "Диалог уже завершён."))
    (let* ((q (nth (dialog-session-idx session) questions))
           (field (qget q :field))
           (options (gethash field *labels*)))
      (if (qget q :is-multi)
          (let ((accepted 0)
                (unknown '()))
            (dolist (item items-answer)
              (let ((norm (string-normalize item)))
                (if (gethash norm options)
                    (progn
                      (push (cons field norm) (dialog-session-prefs session))
                      (incf accepted))
                    (push item unknown))))
            (when (zerop accepted)
              (error "Неизвестные значения: ~{~a~^, ~}" unknown))
            (push accepted (dialog-session-answer-counts session))
            (incf (dialog-session-idx session))
            t)
          (let ((norm (string-normalize text-answer)))
            (unless (gethash norm options)
              (error "Неизвестное значение. Ваш ответ: ~a" text-answer))
            (push (cons field norm) (dialog-session-prefs session))
            (push 1 (dialog-session-answer-counts session))
            (incf (dialog-session-idx session))
            t)))))

(defun calculate-total-paths ()
  (let ((total 1))
    (dolist (q (default-questions))
      (let ((num (length (gethash (qget q :field) *options*))))
        (if (qget q :is-multi)
            (setf total (* total (1- (expt 2 num))))
            (setf total (* total num)))))
    total))

(defun format-recommendations (recs)
  (loop for rec in recs
        for info = (getf rec :info)
        collect
        (list :title (getf rec :title)
              :score (getf rec :score)
              :matched (getf rec :matched)
              :author (getf info :автор)
              :genre (getf info :жанр)
              :epoch (getf info :эпоха)
              :mood (getf info :настроение)
              :difficulty (getf info :сложность)
              :volume (getf info :объём)
              :image (getf info :изображение))))
