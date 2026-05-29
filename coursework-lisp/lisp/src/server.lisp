(in-package :expert/server)

(defvar *initialized* nil)

(defun jq (s)
  (format nil "\"~a\""
          (with-output-to-string (o)
            (loop for c across (princ-to-string s)
                  do (case c
                       (#\" (write-string "\\\"" o))
                       (#\\ (write-string "\\\\" o))
                       (t (write-char c o)))))))

(defun jbool (x) (if x "true" "false"))

(defun out (json)
  (format t "~a~%" json)
  (force-output))

(defun err (msg)
  (out (format nil "{\"status\":\"error\",\"message\":~a}" (jq msg))))

(defun split (line)
  (loop with start = 0
        for i from 0 to (length line)
        when (or (= i (length line)) (char= (char line i) #\|))
          collect (subseq line start i)
          and do (setf start (1+ i))))

(defun ensure-init ()
  (unless *initialized* (error "Система не инициализирована")))

(defun json-init ()
  (let ((count (init-books)))
    (build-rules)
    (setf *initialized* t)
    (format nil "{\"status\":\"ok\",\"frames_count\":~d,\"books_count\":~d}"
            count count)))

(defun json-health ()
  (format nil "{\"status\":\"ok\",\"initialized\":~a,\"books\":~d}"
          (jbool *initialized*) (length *books*)))

(defun json-questions ()
  (ensure-init)
  (format nil "{\"status\":\"ok\",\"questions\":[~{~a~^,~}]}"
          (loop for q in (default-questions)
                for field = (qget q :field)
                collect (format nil
                                "{\"id\":~a,\"field\":~a,\"text\":~a,\"is_multi\":~a,\"available_answers\":~a}"
                                (jq (qget q :id)) (jq field) (jq (qget q :prompt))
                                (jbool (qget q :is-multi))
                                (format nil "[~{~a~^,~}]" (mapcar #'jq (hints-for field)))))))

(defun json-frames ()
  (ensure-init)
  (format nil "{\"status\":\"ok\",\"frames\":[~{~a~^,~}]}"
          (loop for book in *books*
                collect (format nil "{\"id\":~a,\"title\":~a}"
                                (jq (getf book :id))
                                (jq (getf book :title))))))

(defun json-rules (rule-type limit)
  (ensure-init)
  (let* ((info (get-rules-info :rule-type rule-type :limit limit))
         (rules (getf info :rules)))
    (format nil
            "{\"status\":\"ok\",\"total_rules\":~d,\"init_rules_count\":~d,\"match_rules_count\":~d,\"rules\":[~{~a~^,~}]}"
            (getf info :total_rules) (getf info :init_rules_count) (getf info :match_rules_count)
            (mapcar (lambda (r)
                      (format nil "{\"name\":~a,\"type\":~a,\"description\":~a}"
                              (jq (getf r :name)) (jq (getf r :type)) (jq (getf r :description))))
                    rules))))

(defun json-items (items)
  (format nil "[~{~a~^,~}]"
          (mapcar (lambda (it)
                    (format nil
                            "{\"title\":~a,\"score\":~d,\"matched\":[~{~a~^,~}],\"author\":~a,\"genre\":~a,\"epoch\":~a,\"mood\":~a,\"difficulty\":~a,\"volume\":~a,\"image\":~a}"
                            (jq (getf it :title)) (getf it :score)
                            (mapcar #'jq (getf it :matched))
                            (jq (or (getf it :author) ""))
                            (jq (or (getf it :genre) ""))
                            (jq (or (getf it :epoch) ""))
                            (jq (or (getf it :mood) ""))
                            (jq (or (getf it :difficulty) ""))
                            (jq (or (getf it :volume) ""))
                            (jq (or (getf it :image) ""))))
                  items)))

(defun json-submit-answers (top-k payload)
  (ensure-init)
  (format nil "{\"status\":\"ok\",\"items\":~a}"
          (json-items (submit-answers payload (parse-integer top-k)))))

(defun handle-line (line)
  (let* ((parts (split line))
         (cmd (string-downcase (first parts))))
    (cond
      ((string= cmd "init") (json-init))
      ((string= cmd "health") (json-health))
      ((string= cmd "get_questions") (json-questions))
      ((string= cmd "get_frames") (json-frames))
      ((string= cmd "get_rules")
       (json-rules (second parts) (when (third parts) (parse-integer (third parts)))))
      ((string= cmd "submit_answers")
       (json-submit-answers (second parts) (third parts)))
      (t (error "Unknown command: ~a" cmd)))))

(defun run-server ()
  (out "{\"status\":\"ok\",\"message\":\"Lisp expert system ready\"}")
  (loop for line = (read-line *standard-input* nil nil)
        while line
        do (handler-case (out (handle-line line))
             (error (e) (err (format nil "~a" e))))))
