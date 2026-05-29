(in-package :cl)

(defun load-expert-system (src-dir)
  (load (merge-pathnames "packages.lisp" src-dir))
  (load (merge-pathnames "books.lisp" src-dir))
  (load (merge-pathnames "frames.lisp" src-dir))
  (load (merge-pathnames "engine.lisp" src-dir))
  (load (merge-pathnames "dialog.lisp" src-dir))
  (load (merge-pathnames "server.lisp" src-dir)))

(load-expert-system (directory-namestring *load-truename*))
(in-package :expert/server)
(run-server)
