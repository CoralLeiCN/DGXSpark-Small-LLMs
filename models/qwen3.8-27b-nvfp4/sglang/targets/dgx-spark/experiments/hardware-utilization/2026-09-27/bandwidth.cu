#include <cuda_runtime.h>
#include <cstdio>
#include <cstdlib>
#include <cmath>
#include <string>
#define CK(x) do { cudaError_t e=(x); if(e!=cudaSuccess){fprintf(stderr,"%s: %s\n",#x,cudaGetErrorString(e)); return 1;} } while(0)
__global__ void init(float *x, size_t n) { for(size_t i=blockIdx.x*blockDim.x+threadIdx.x;i<n;i+=size_t(gridDim.x)*blockDim.x)x[i]=1.0f; }
__global__ void bw_read(const float *x,float *sink,size_t n){
 float v=0; for(size_t i=blockIdx.x*blockDim.x+threadIdx.x;i<n;i+=size_t(gridDim.x)*blockDim.x)v+=x[i];
 for(int d=16;d>0;d/=2)v+=__shfl_down_sync(0xffffffff,v,d);
 if((threadIdx.x&31)==0)sink[blockIdx.x*(blockDim.x/32)+threadIdx.x/32]=v;
}
__global__ void bw_write(float *y,size_t n){ for(size_t i=blockIdx.x*blockDim.x+threadIdx.x;i<n;i+=size_t(gridDim.x)*blockDim.x)y[i]=3.0f; }
__global__ void bw_copy(const float *x,float *y,size_t n){ for(size_t i=blockIdx.x*blockDim.x+threadIdx.x;i<n;i+=size_t(gridDim.x)*blockDim.x)y[i]=x[i]; }
int main(int argc,char**argv){
 const size_t n=size_t(1)<<27, bytes=n*sizeof(float); const int repeats=argc>1?atoi(argv[1]):40;
 cudaDeviceProp p; CK(cudaGetDeviceProperties(&p,0)); const int blocks=p.multiProcessorCount*32;
 float *x,*y,*sink; CK(cudaMalloc(&x,bytes));CK(cudaMalloc(&y,bytes)); CK(cudaMalloc(&sink,blocks*8*sizeof(float)));
 init<<<blocks,256>>>(x,n); CK(cudaDeviceSynchronize());
 cudaEvent_t a,b; CK(cudaEventCreate(&a));CK(cudaEventCreate(&b));
 printf("{\"device\":\"%s\",\"buffer_bytes\":%zu,\"l2_bytes\":%d,\"sm_count\":%d}\n",p.name,bytes,p.l2CacheSize,p.multiProcessorCount);
 for(int mode=0;mode<3;mode++) for(int trial=1;trial<=3;trial++){
  auto launch=[&](){if(mode==0)bw_read<<<blocks,256>>>(x,sink,n);else if(mode==1)bw_write<<<blocks,256>>>(y,n);else bw_copy<<<blocks,256>>>(x,y,n);};
  for(int i=0;i<5;i++)launch(); CK(cudaDeviceSynchronize()); CK(cudaEventRecord(a));
  for(int i=0;i<repeats;i++)launch(); CK(cudaEventRecord(b)); CK(cudaEventSynchronize(b));CK(cudaGetLastError());
  float ms;CK(cudaEventElapsedTime(&ms,a,b)); bool valid=true;
  if(mode==0){float *h=(float*)malloc(blocks*8*sizeof(float));CK(cudaMemcpy(h,sink,blocks*8*sizeof(float),cudaMemcpyDeviceToHost));double sum=0;for(int i=0;i<blocks*8;i++)sum+=h[i];valid=fabs(sum-double(n))<double(n)*1e-6;free(h);}
  else {float first,last;CK(cudaMemcpy(&first,y,sizeof(float),cudaMemcpyDeviceToHost));CK(cudaMemcpy(&last,y+n-1,sizeof(float),cudaMemcpyDeviceToHost)); valid=first==(mode==1?3.0f:1.0f)&&last==first;}
  printf("{\"pattern\":\"%s\",\"trial\":%d,\"repeats\":%d,\"ms\":%.6f,\"effective_GBps\":%.6f,\"valid\":%s}\n",mode==0?"read":mode==1?"write":"copy",trial,repeats,ms,double(bytes)*(mode==2?2:1)*repeats/ms/1e6,valid?"true":"false");fflush(stdout);if(!valid)return 2;
 }
 CK(cudaFree(x));CK(cudaFree(y));CK(cudaFree(sink));return 0;
}
