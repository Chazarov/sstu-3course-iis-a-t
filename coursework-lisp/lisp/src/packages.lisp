(in-package :cl)

(defpackage :expert/frames
  (:use :cl)
  (:export #:init-books #:string-normalize #:human-label #:raw-get
           #:*books* #:*options* #:*labels*))

(defpackage :expert/engine
  (:use :cl :expert/frames)
  (:export #:build-rules #:get-recommendations #:get-all-recommendations
           #:get-rules-info))

(defpackage :expert/dialog
  (:use :cl :expert/frames :expert/engine)
  (:export #:default-questions #:hints-for #:qget
           #:submit-answers #:format-recommendations))

(defpackage :expert/server
  (:use :cl :expert/frames :expert/engine :expert/dialog)
  (:export #:run-server))

(in-package :expert/server)
