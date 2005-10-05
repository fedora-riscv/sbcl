(lambda (features)
  (flet ((enable (x)
           (pushnew x features))
         (disable (x)
           (setf features (remove x features))))
    ;; Threading support, available on x86/x86-64 Linux only.
    (enable :sb-thread))) 
