; This program is to synthesize enhanced audio samples.
; Assuming 5 Bands of frequency to be processed.
;Number of frequency bands is 5 , move to R2
mov 5 0 2 0 1 0 0 0001
;PC jump value is 6 move to R3
mov d 0 3 0 1 0 0 0001
; Move base addresses for data storage
mov 100 0 5 0 1 0 0 0001
mov 120 0 6 0 1 0 0 0001
mov 140 0 7 0 1 0 0 0001
mov 160 0 8 0 1 0 0 0001
mov 180 0 9 0 1 0 0 0001
;mov 200 0 a 0 1 0 0 0001
mov 220 0 b 0 1 0 0 0001
mov 240 0 c 0 1 0 0 0001
mov 260 0 d 0 1 0 0 0001
mov 280 0 e 0 1 0 0 0001
mov 300 0 f 0 1 0 0 0001
mov 320 0 10 0 1 0 0 0001
;final Result address
mov 400 0 11 0 1 0 0 0001
mov 450 0 12 0 1 0 0 0001
mov f 0 13 0 1 0 0 0001
;Choose time/frequency domain implementation based on result of Correlation
correlation 100 3 200 3 0 0 0 0000
;the branch statement decides whether the Freq Domain/time domain
; If the Correlation result is greater than 0, then use Freq domain
if 200 3 0 0 1 0 8 0000
; TIME DOMAIN
; Loop for Number of frequency bands
; Loop counter is in R4, and the loop count is in R2
lbeg 5 4 0 0 0 0 0 0001
; Series of FIR filters - Addresses are stored in R5, R6, R7, R8, R9, R10
complex_fir 5 3 6 3 0 0 1 0000
adaptive_fir 6 3 7 3 0 0 1 0000
real_fir 7 3 8 3 0 0 1 0000
real_fir 8 3 9 3 0 0 1 0000
;Update all the addresses based on the loop counter
add 4 5 5 0 0 0 1 0000
add 4 6 6 0 0 0 1 0000
add 4 7 7 0 0 0 1 0000
add 4 8 8 0 0 0 1 0000
add 4 9 9 0 0 0 1 0000
;Loop ends
lend 0 4 0 0 0 0 0 0001
; accumulate the results
vector_add 9 3 11 3 0 0 1 0001
; The branch ends here
jump 0 13 0 0 0 0 8 0000
;FREQ DOMAIN - this is where the jump lands
lbeg 5 a 0 0 0 0 0 0001
;perform fft on the input
fft_256 5 3 b 3 0 0 1 0000
;FIR becomes multiplication in freq domain
vector_dot b 3 c 3 0 0 1 0000 
vector_dot c 3 d 3 0 0 1 0000 
vector_dot d 3 e 3 0 0 1 0000 
vector_dot e 3 f 3 0 0 1 0000 
;perform inverse FFT
fft_256 f 3 10 3 0 0 1 0001
;Update all the addresses based on the loop counter
add a b b 0 0 0 1 0000
add a c c 0 0 0 1 0000
add a d d 0 0 0 1 0000
add a e e 0 0 0 1 0000
add a f f 0 0 0 1 0000
add a 10 10 0 0 0 1 0000
;loop ends here
lend 0 a 0 0 0 0 0 0001
;accumulate the results
vector_add 10 3 12 3 0 0 1 0001
;DONE!
mov 100 0 5 0 1 0 0 0001
mov 100 0 5 0 1 0 0 0001
