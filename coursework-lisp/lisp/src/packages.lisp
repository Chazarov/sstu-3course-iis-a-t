(in-package :cl)

(defpackage :expert/json
  (:use :cl)
  (:export #:json-decode #:json-encode))

(defpackage :expert/frames
  (:use :cl)
  (:export #:init-books
           #:string-normalize
           #:human-label
           #:*books*
           #:*options*
           #:*labels*))

(defpackage :expert/engine
  (:use :cl :expert/frames)
  (:export #:build-rules
           #:get-recommendations
           #:get-all-recommendations
           #:get-rules-info
           #:*rules*))

(defpackage :expert/dialog
  (:use :cl :expert/frames :expert/engine)
  (:export #:new-session
           #:session-is-done
           #:session-can-go-back
           #:session-go-back
           #:session-add-answer
           #:session-question
           #:session-prefs
           #:default-questions
           #:calculate-total-paths
           #:format-recommendations))

(defpackage :expert/server
  (:use :cl :expert/json :expert/frames :expert/engine :expert/dialog)
  (:export #:handle-request #:run-server))

(in-package :expert/server)
