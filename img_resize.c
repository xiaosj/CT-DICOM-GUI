#include <stdio.h>
#include <stdlib.h>

// Generate bin index and ratio
void bin_ratio(int nnx, float ndx, int nx, float dx, float *x_loc, int *x_idx, float *x_ratio) {
    int   width_ratio = (int)(ndx / dx) + 2;

    for(int ix = 0; ix <= nnx; ix++) {
        x_loc[ix] = (int)(ix - nnx / 2) * ndx / dx + (int)(nx / 2);
    }

    for (int i = 0; i < nnx * width_ratio; i++) {
        x_idx[i] = 0;
        x_ratio[i] = 1.0;
    }

    for (int i = 0; i < nnx; i++) {
        float x0 = x_loc[i];
        float x1 = x_loc[i + 1];
        int i0 = (int)x0;
        int i1 = (int)x1;
        if(i1 < x1)  i1++;

        int idx0 = i * width_ratio;
        if(i1 - i0 == width_ratio) {
            x_ratio[idx0 + width_ratio - 1] = x1 - i1 + 1;
        } else if(i1 - i0 == width_ratio - 1){
            x_ratio[idx0 + width_ratio - 2] = x1 - i1 + 1;
            x_ratio[idx0 + width_ratio - 1] = 0.;
        } else if(i1 - i0 == width_ratio - 2) {
            x_ratio[idx0 + width_ratio - 3] = x1 - i1 + 1;
            x_ratio[idx0 + width_ratio - 2] = 0.;
            x_ratio[idx0 + width_ratio - 1] = 0.;
        }
        x_ratio[idx0] = i0 + 1 - x0;
        for(int j = 0; j < i1 - i0; j++) {
            x_idx[idx0 + j] = i0 + j;
        }
    }
}


int main(int argc, char *argv[]) {
    char  *filename;
    FILE  *finp;
    short *img;
    int    nx, ny, nz;
    float  dx, dy, dz;

    short *nimg;
    int    nnx, nny, nnz;
    float  ndx, ndy, ndz;

    if(argc != 5) {
        printf("Wring input format. Please use (new voxel size in the unit of mm):\n");
        printf("img_resize [img_file] [new_dx] [new_dy] [new_dz]\n");
        return -1;
    } else {
        filename = argv[1];
        ndx = atof(argv[2]);
        ndy = atof(argv[3]);
        ndz = atof(argv[4]);
        printf("Resizing %s ...\n", filename);
    }

    finp = fopen(filename, "rb");
    if(finp == NULL) {
        printf("Cannot open file %s\n", filename);
        return -2;
    }

    // Read original voxel information
    fread(&nx, sizeof(int), 1, finp);
    fread(&ny, sizeof(int), 1, finp);
    fread(&nz, sizeof(int), 1, finp);
    fread(&dx, sizeof(float), 1, finp);
    fread(&dy, sizeof(float), 1, finp);
    fread(&dz, sizeof(float), 1, finp);
    printf("Original data are %d x %d x %d with %.3f x %.3f x %.3f mm each\n", nx, ny, nz, dx, dy, dz);
    img = calloc(sizeof(short), nx * ny * nz);
    if(img == NULL) {
        printf("Fail to allocate memory.\n");
        return -2;
    }
    fread(img, sizeof(short), nx * ny * nz, finp);
    fclose(finp);

    // New voxel numbers
    nnx = (int)(nx / 2 * dx / ndx) * 2;
    nny = (int)(ny / 2 * dy / ndy) * 2;
    nnz = (int)(nz / 2 * dz / ndz) * 2;
    printf(" --> New data are %d x %d x %d with %.3f x %.3f x %.3f mm each\n", nnx, nny, nnz, ndx, ndy, ndz);

    // Resize the CT data
    int   width_ratio_x = (int)(ndx / dx) + 2;
    float *x_loc = calloc(nnx+1, sizeof(float));
    int   *x_idx = calloc(nnx * width_ratio_x, sizeof(int));;
    float *x_ratio = calloc(nnx * width_ratio_x, sizeof(float));
    bin_ratio(nnx, ndx, nx, dx, x_loc, x_idx, x_ratio);

    int width_ratio_y = (int)(ndy / dy) + 2;
    float *y_loc = calloc(nny+1, sizeof(float));
    int   *y_idx = calloc(nny * width_ratio_y, sizeof(int));;
    float *y_ratio = calloc(nny * width_ratio_y, sizeof(float));
    bin_ratio(nny, ndy, ny, dy, y_loc, y_idx, y_ratio);

    int width_ratio_z = (int)(ndz / dz) + 2;
    float *z_loc = calloc(nnz+1, sizeof(float));
    int   *z_idx = calloc(nnz * width_ratio_z, sizeof(int));;
    float *z_ratio = calloc(nnz * width_ratio_z, sizeof(float));
    bin_ratio(nnz, ndz, nz, dz, z_loc, z_idx, z_ratio);

    nimg = calloc(nnx * nny * nnz, sizeof(short));
    if(img == NULL) {
        printf("Fail to allocate memory.\n");
        return -2;
    }
    int nix, niy, niz;
    int idx, nidx, idx_base = 0;
    int pcount = 0;
    float voxel_ratio = dx * dy * dz / (ndx * ndy *ndz);
    for(niz = 0; niz < nnz; niz++) {
        int iz_base = niz * width_ratio_z;
        for(niy = 0; niy < nny; niy++) {
            int iy_base = niy * width_ratio_y;
            for(nix = 0; nix < nnx; nix++) {
                int ix_base = nix * width_ratio_x;
                float value = 0;
                for(int iz = 0; iz < width_ratio_z; iz++) {
                    int   idx_z = z_idx[iz_base + iz];
                    float ratio_z = z_ratio[iz_base + iz];
                    for(int iy = 0; iy < width_ratio_y; iy++) {
                        int idx_y = y_idx[iy_base + iy];
                        float ratio_y = y_ratio[iy_base + iy];
                        for(int ix = 0; ix < width_ratio_x; ix++) {
                            int idx_x = x_idx[ix_base + ix];
                            float ratio_x = x_ratio[ix_base + ix];
                            int idx = idx_z * nx * ny + idx_y * nx + idx_x;
                            value += img[idx] * ratio_x * ratio_y * ratio_z;
                        }
                    }
                }
                nimg[idx_base + nix] = (short)(value * voxel_ratio);
            }
            idx_base += nnx;
        }
        printf("%d%%\r", niz * 100 / nnz);
        fflush(stdout);
    }
    printf("Done  \n");

    // Write the enw img file
    FILE  *fout;
    char outfile[256];
    sprintf(outfile, "%s_new", filename);
    fout = fopen(outfile, "wb");
    fwrite(&nnx, sizeof(int), 1, fout);
    fwrite(&nny, sizeof(int), 1, fout);
    fwrite(&nnz, sizeof(int), 1, fout);
    fwrite(&ndx, sizeof(float), 1, fout);
    fwrite(&ndy, sizeof(float), 1, fout);
    fwrite(&ndz, sizeof(float), 1, fout);
    fwrite(nimg, sizeof(short), nnx * nny * nnz, fout);
    fclose(fout);

    // Release arrays
    free(img);
    free(nimg);
    free(x_loc);
    free(x_idx);
    free(x_ratio);
    free(y_idx);
    free(y_loc);
    free(y_ratio);
    free(z_loc);
    free(z_idx);
    free(z_ratio);
}