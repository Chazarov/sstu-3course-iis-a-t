(in-package :expert/frames)

(defparameter *books* '())
(defparameter *options* (make-hash-table :test 'equal))
(defparameter *labels* (make-hash-table :test 'equal))

(defparameter *match-fields*
  '("автор" "жанр" "эпоха" "направление" "сложность" "объём"
    "настроение" "тип_конфликта" "тип_героя" "темы" "художественные_средства"))

(defparameter *list-fields* '("темы" "художественные_средства"))

(defun string-normalize (value)
  (string-downcase
   (substitute #\_ #\space (string-trim '(#\space) (princ-to-string value)))))

(defun raw-get (raw key)
  (getf raw (intern (string-upcase key) :keyword)))

(defun init-books ()
  (setf *books* (copy-list +books-data+))
  (build-options)
  (build-label-map)
  (length *books*))

(defun build-options ()
  (clrhash *options*)
  (dolist (field *match-fields*)
    (setf (gethash field *options*) '()))
  (dolist (book *books*)
    (dolist (field *match-fields*)
      (let ((val (raw-get (getf book :raw) field)))
        (when val
          (let ((bucket (gethash field *options*)))
            (if (and (member field *list-fields* :test #'equal) (listp val))
                (dolist (item val)
                  (pushnew (princ-to-string item) bucket :test #'equal))
                (when (stringp val)
                  (pushnew val bucket :test #'equal)))
            (setf (gethash field *options*) bucket))))))
  (maphash (lambda (k v)
             (when v
               (setf (gethash k *options*) (sort (copy-list v) #'string<))))
           *options*))

(defun build-label-map ()
  (clrhash *labels*)
  (maphash
   (lambda (field vals)
     (let ((m (make-hash-table :test 'equal)))
       (dolist (v vals)
         (setf (gethash (string-normalize v) m) v))
       (setf (gethash field *labels*) m)))
   *options*))

(defun human-label (field value)
  (let ((m (gethash field *labels*)))
    (if m (or (gethash value m) value) value)))
