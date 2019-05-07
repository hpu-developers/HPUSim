void matrix_mult_wiki_block(const float*A , const float* B, float* C,
                            const int N, const int M, const int K) {
    const int block_size = 64 / sizeof(float); // 64 = common cache line size
    for(int i=0; i<N; i++) {
        for(int j=0; j<K; j++) {
            C[K*i + j] = 0;
        }
    }
    for (int i0 = 0; i0 < N; i0 += block_size) {
        int imax = i0 + block_size <= N ? i0 + block_size: N;

        for (int j0 = 0; j0 < M; j0 += block_size) {
            int jmax = j0 + block_size <= M ? j0 + block_size: M;

            for (int k0 = 0; k0 < K; k0 += block_size) {
                int kmax = k0 + block_size <= K ? k0 + block_size: K;

                for (int j1 = j0; j1 < jmax; ++j1) {
                    int sj = M * j1;

                    for (int i1 = i0; i1 < imax; ++i1) {
                        int mi = M * i1;
                        int ki = K * i1;
                        int kij = ki + j1;

                        for (int k1 = k0; k1 < kmax; ++k1) {
                            C[kij] = C[kij]+A[mi + k1] * B[sj + k1];
                        }
                    }
                }
            }
        }
    }
}
