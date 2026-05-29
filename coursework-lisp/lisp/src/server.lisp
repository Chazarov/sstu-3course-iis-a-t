(in-package :expert/server)

(defvar *initialized* nil)

(defun response-ok (&rest pairs)
  (list* :status "ok" pairs))

(defun response-error (message)
  (list :status "error" :message message))

(defun ensure-initialized ()
  (unless *initialized*
    (error "Expert system is not initialized. Call init first.")))

(defun hash-table->alist (ht)
  (let ((result '()))
    (maphash (lambda (k v) (push (cons k v) result)) ht)
    (sort result #'string< :key #'car)))

(defun nested-hash-table->alist (ht)
  (let ((result '()))
    (maphash
     (lambda (k v)
       (if (hash-table-p v)
           (push (cons k (hash-table->alist v)) result)
           (push (cons k v) result)))
     ht)
    (sort result #'string< :key #'car)))

(defun frames->json-list ()
  (loop for book in *books*
        collect (list :id (getf book :id)
                      :title (getf book :title)
                      :raw (getf book :raw)
                      :match (getf book :match))))

(defun handle-init (req)
  (declare (ignore req))
  (let ((count (init-books)))
    (build-rules)
    (setf *initialized* t)
    (response-ok :frames_count count :rules_count (length *rules*))))

(defun handle-health ()
  (response-ok :initialized *initialized*
               :books (length *books*)
               :rules (length *rules*)))

(defun handle-get-labels ()
  (ensure-initialized)
  (response-ok :labels (hash-table->alist *options*)))

(defun handle-get-options ()
  (ensure-initialized)
  (response-ok :options (nested-hash-table->alist *labels*)))

(defun handle-get-frames ()
  (ensure-initialized)
  (response-ok :frames (frames->json-list)))

(defun handle-get-rules (req)
  (ensure-initialized)
  (let ((info (get-rules-info :rule-type (getf req :rule_type)
                              :limit (getf req :limit))))
    (append (response-ok) info)))

(defun handle-recommend (req)
  (ensure-initialized)
  (let* ((prefs-raw (getf req :prefs))
         (top-k (or (getf req :top_k) 5))
         (prefs (mapcar (lambda (p) (cons (first p) (second p))) prefs-raw)))
    (response-ok :items (get-recommendations prefs :top-k top-k))))

(defun handle-get-all-recommendations ()
  (ensure-initialized)
  (response-ok :items (get-all-recommendations)))

(defun handle-dialog-new ()
  (ensure-initialized)
  (response-ok :session_id (new-session)))

(defun handle-dialog-is-done (req)
  (ensure-initialized)
  (response-ok :done (session-is-done (getf req :session_id))))

(defun handle-dialog-can-go-back (req)
  (ensure-initialized)
  (response-ok :can_go_back (session-can-go-back (getf req :session_id))))

(defun handle-dialog-go-back (req)
  (ensure-initialized)
  (handler-case
      (progn
        (session-go-back (getf req :session_id))
        (response-ok))
    (error (e) (response-error (format nil "~a" e)))))

(defun handle-dialog-question (req)
  (ensure-initialized)
  (let ((question (session-question (getf req :session_id))))
    (if question
        (append (response-ok) question)
        (response-ok :done t))))

(defun handle-dialog-add-answer (req)
  (ensure-initialized)
  (handler-case
      (progn
        (session-add-answer (getf req :session_id)
                            :text-answer (getf req :text_answer)
                            :items-answer (getf req :items_answer))
        (response-ok))
    (error (e) (response-error (format nil "~a" e)))))

(defun handle-dialog-recommend (req)
  (ensure-initialized)
  (let* ((session-id (getf req :session_id))
         (top-k (or (getf req :top_k) 5))
         (prefs (reverse (session-prefs session-id)))
         (recs (get-recommendations prefs :top-k top-k)))
    (response-ok :items (format-recommendations recs))))

(defun handle-request (req)
  (let ((cmd (string-downcase (getf req :cmd))))
    (cond
      ((string= cmd "init") (handle-init req))
      ((string= cmd "health") (handle-health))
      ((string= cmd "get_labels") (handle-get-labels))
      ((string= cmd "get_options") (handle-get-options))
      ((string= cmd "get_frames") (handle-get-frames))
      ((string= cmd "get_rules") (handle-get-rules req))
      ((string= cmd "recommend") (handle-recommend req))
      ((string= cmd "get_all_recommendations") (handle-get-all-recommendations))
      ((string= cmd "dialog_new") (handle-dialog-new))
      ((string= cmd "dialog_is_done") (handle-dialog-is-done req))
      ((string= cmd "dialog_can_go_back") (handle-dialog-can-go-back req))
      ((string= cmd "dialog_go_back") (handle-dialog-go-back req))
      ((string= cmd "dialog_question") (handle-dialog-question req))
      ((string= cmd "dialog_add_answer") (handle-dialog-add-answer req))
      ((string= cmd "dialog_recommend") (handle-dialog-recommend req))
      (t (response-error (format nil "Unknown command: ~a" cmd))))))

(defun run-server ()
  (format t "~a~%" (json-encode (response-ok :message "Lisp expert system ready")))
  (force-output)
  (loop
    (let ((line (read-line *standard-input* nil nil)))
      (unless line (return))
      (handler-case
          (let* ((req (json-decode line))
                 (resp (handle-request req)))
            (format t "~a~%" (json-encode resp))
            (force-output))
        (error (e)
          (format t "~a~%" (json-encode (response-error (format nil "~a" e))))
          (force-output))))))
