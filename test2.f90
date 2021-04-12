      program HELLOWORLD
!-----------------------------------------
! Our first readable program
!-----------------------------------------
      character(len=20) :: text1
! the text string
      text1 = 'Hello world!'
! print the text to screen
      write (6,*) text1
      end program
