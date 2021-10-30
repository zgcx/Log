#include "cuda_runtime.h"
#include "device_launch_parameters.h"

#include "thrust/host_vector.h"
#include "thrust/device_vector.h"
#include "thrust/extrema.h"
#include "thrust/reduce.h"
#include "thrust/functional.h"
#include "thrust/execution_policy.h"

#include "gdal_util.h"
#include "cpl_conv.h"


template<typename T1, typename T2>
struct type2_type
{
	__host__ __device__ T2 operator()(const T1& x) const
	{
		return static_cast<T2>(x);
	}
};

struct variance : std::unary_function<us, double>
{
	variance(double m) : mean(m) { }
	const double mean;
	__host__ __device__ double operator()(us data) const
	{
		return std::pow(data - mean, 2.0);
	}
};

// atomicCAS 暂不支持 uc

__global__ void pixels_std(us* data, uc* res, const ull size, us band_max, us band_min, us uc_max, us uc_min, float k, float b)
{
	ui tid = threadIdx.x + blockDim.x * blockIdx.x;
	if (tid >= size) return;

	const us d = data[tid];
	us v;
	if (d == band_min)
		v = band_min;
	else if (d <= uc_min)
		v = band_min;
	else if (d >= uc_max)
		v = band_max;
	else if (k * d + b < band_min)
		v = band_min;
	else if (k * d + b > band_max)
		v = band_max;
	else if (k * d + b > band_min && k * d + b < band_max)
		v = k * d + b;
	else
		v = d;

	res[tid] = static_cast<uc>(v);
}

int main(int argc, char* argv[])
{
	// 16bit 转 8bit
	GDALAllRegister();

	char psz_filename[1024] = "D:\\统筹影像\\cuda\\PAN31.TIF";
	char psz_filename_new[1024] = "D:\\统筹影像\\cuda\\PANNew.TIF";

	GDALDriver* tifDriver = GetGDALDriverManager()->GetDriverByName("GTiff");
	CPLSetConfigOption("GDAL_FILENAME_IS_UTF8", "NO");
	const GDALDatasetH dataset_16bit = GDALOpen(psz_filename, GA_Update);
	
	// if (dataset == NULL)
	raster_info ri;
	get_raster_info(dataset_16bit, &ri);

	GDALDataset* dataset_8bit = tifDriver->Create(psz_filename_new, ri.width, ri.height, GDALGetRasterCount(dataset_16bit), GDT_Byte,NULL);
	dataset_8bit->SetGeoTransform(ri.geo_transform);
	dataset_8bit->SetProjection(ri.projection);

	printf("Size is %dx%dx%d\n",
		ri.width,
		ri.height,
		GDALGetRasterCount(dataset_8bit));
	printf("Pixel Size = (%.6f,%.6f)\n",
		ri.geo_transform[1], ri.geo_transform[5]);

	cudaError_t status;
	GDALRasterBandH h_band_16;
	GDALRasterBandH h_band_8;
	const int x_size = ri.width;
	const int y_size = ri.height;
	const ull size = x_size * y_size;
	const ull malloc_size = sizeof(us) * x_size * y_size;

	// 原影像
	us* h_data;
	uc* h_res;
	h_data = (us*)CPLMalloc(malloc_size);
	h_res = (uc*)CPLMalloc(size);
	// 新影像
	us* d_data;
	uc* d_res;
	status = cudaMalloc((void**)&d_data, malloc_size);
	status = cudaMalloc((void**)&d_res, size);
	for (int i = 0; i < 3; ++i)
	{
		h_band_16 = GDALGetRasterBand(dataset_16bit, i + 1);
		h_band_8 = GDALGetRasterBand(dataset_8bit, i + 1);
		GDALRasterIO(h_band_16, GF_Read, 0, 0, x_size, y_size,
			h_data, x_size, y_size, GDT_UInt16, 0, 0);
		// 拷贝数组大小有误
		status = cudaMemcpy(d_data, h_data, malloc_size, cudaMemcpyHostToDevice);
		thrust::device_ptr<us> ptr(d_data);
		// 数组越界时抛出 msg:extrema failed to synchronize
		// 最大值最小值仅为测试函数
		const auto max_iter = thrust::max_element(ptr, ptr + size);
		const auto min_iter = thrust::min_element(ptr, ptr + size);
		us band_max = *max_iter;
		us band_min = *min_iter;
		band_max = 255;
		band_min = 0;
		// cpu 执行
		// auto band_sum_cpu = thrust::reduce(thrust::host, h_data, h_data + size, (ull)0);
		// gpu 执行
		auto band_sum = thrust::reduce(ptr, ptr + size, (ull)0);
		double band_mean = band_sum / (double)size;
		// 方差 (val-mean)*(val-mean)
		auto band_std2 = thrust::transform_reduce(ptr, ptr + size, variance(band_mean), (double)0, thrust::plus<double>());

		double band_std = std::sqrt(band_std2/(double)(size-1));
		float kn = 2.5;
		float uc_max = band_mean + kn * band_std;
		float uc_min = band_mean - kn * band_std;
		float k = (band_max - band_min) / (uc_max - uc_min);
		float b = (uc_max * band_min - uc_min * band_max) / (uc_max - uc_min);
		if (uc_min <= 0)
			uc_min = 0;

		// 标准差
		const ui block_size = 128;
		const ui grid_size = (size - 1) / block_size + 1;
		pixels_std << <grid_size, block_size >> > (d_data, d_res, size, band_max, band_min, uc_max, uc_min, k, b);

		cudaDeviceSynchronize();

		cudaMemcpy(h_res, d_res, size, cudaMemcpyDeviceToHost);
		//
		GDALRasterIO(h_band_8, GF_Write, 0, 0, x_size, y_size,
			h_res, x_size, y_size, GDT_Byte,0, 0);
	}
	cudaFree(d_data);
	cudaFree(d_res);
	CPLFree(h_data);
	CPLFree(h_res);
	
	GDALClose(dataset_16bit);
	GDALClose(dataset_8bit);
	
	return 0;
}

