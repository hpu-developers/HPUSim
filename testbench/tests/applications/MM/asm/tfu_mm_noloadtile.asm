;TFU ASM is provided here
; THIS ASM IS GARBAGE. NOT THOUGHT THROUGH Indexes can be wrong
;N,K,M
;allocate Mshared BS*BS
;allocate Nshared BS*BS
;
;loop_matrix: for i=0 .. N/BS .. i++
;                 load_tile amatrix+i*BS*N+i*BS, Mshared+i*BS, N, BS*BS
;                 for j=0;j<N/BS;j++
;                    load_tile bmatrix+N*BS*i+j*BS*N, Nshared+j*BS, N, BS*BS
;                    
;                    matmul Mshared Nshared Cshared BS*BS
;                 store_tile Cshared cmatrix+i*BS*n+i*BS
;                 

;allocate
;N
mov #40 R0
;BS
mov #10 R1
;BS*BS
mul R1 R1 R9
;shared memory allocate
;allocate #30000000 BS*BS
;allocate #10000000 BS*BS
;allocate #20000000 BS*BS
;for i=0,N/BS,i++
;i
mov #0 R2
;M/BS
div R0 R1 R3
lbeg #17 #4 R2
;i*BS
mul R2 R1 R4
;i*BS*N
mul R4 R0 R5
;N*BS*i+i*BS
add R4 R5 R6
;*amatrix
add #5000 R6 R7 
;#30000000+i*BS
add #30000000 R4 R8
load_tile R7 R1 R8
;j=0
mov #0 R10
lbeg #C #4 R10 
;i*BS*N
mul R4 R0 R11
;BS*N
mul R1 R0 R12 
;j*BS
mul R10 R16 R17
;j*BS*N
mul R10 R12 R13
add R11 R13 R14
;bmatrix + N*BS*i+j*BS*N
add #1000 R14 R15 
add #10000000 R17 R18
load_tile R15 R1 R18
matmul #30000000 R9 #10000000 R9 #20000000 R9
;j++
add R10 #1 R10
lend 
add #2000 R6 R19 
;store_tile cshared R1 R19
add R2 #1 R2 
lend
mov R21 R22
end


;__global__ void matrixMultiplyShared(float *A, float *B, float *C, int numARows, int numAColumns,int numBRows, int numBColumns,int numCRows, int numCColumns) {
;  int bx = blockIdx.x, by = blockIdx.y;
;  int tx = threadIdx.x, ty = threadIdx.y;
;  
;  int Row = by * TILE_WIDTH + ty;
;  int Col = bx * TILE_WIDTH + tx;
;  
;  float Pvalue = 0;
;  for(int ph = 0; ph < ceil(numAColumns / (float)TILE_WIDTH); ph++){
;    if((Row < numARows) && (ph * TILE_WIDTH + tx) < numAColumns)
;      Mds[ty][tx] = A[Row * numAColumns + ph * TILE_WIDTH + tx];
;    else
;      Mds[ty][tx] = 0;
;    if ((ph*TILE_WIDTH+ty) < numBRows && (Col < numBColumns))
;      Nds[ty][tx] = B[(ph * TILE_WIDTH + ty) * numBColumns + Col];
;    else
;      Nds[ty][tx] = 0;
;   
;    __syncthreads();
;    
;    for (int k = 0; k < TILE_WIDTH; ++k) {
;      Pvalue += Mds[ty][k] * Nds[k][tx];
;    }
;    __syncthreads();
;  }
;    if ((Row < numCRows) && (Col < numCColumns)) C[Row * numCColumns + Col] = Pvalue;
;}

