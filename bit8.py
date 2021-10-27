# -*- coding: utf-8 -*-
# @Last Modified Time    : 2020/12/8 8:05
# @Author  : noodles
# @File    : bit8.py
# 标准差拉伸 python 版本 call bit8(...) to stretch the band to 8bit(0-255)

from osgeo import gdal
import numpy as np
import os


def bit8(raw_band_data, d_min, d_max, mean, std_dev, kn):
    uc_max = mean + kn * std_dev
    uc_min = mean - kn * std_dev
    k = (d_max - d_min) / (uc_max - uc_min)
    b = (uc_max * d_min - uc_min * d_max) / (uc_max - uc_min)
    if uc_min <= 0:
        uc_min = 0

    raw_band_data = np.select([raw_band_data == d_min, raw_band_data <= uc_min, raw_band_data >= uc_max, k * raw_band_data + b < d_min, k * raw_band_data + b > d_max ,
                               (k * raw_band_data + b > d_min) & (k * raw_band_data + b < d_max)],
                              [d_min, d_min, d_max, d_min, d_max, k * raw_band_data + b], raw_band_data)
    return raw_band_data


def convert2bit8(in_path):
    if not os.path.exists(in_path):
        print('输入路径不存在！')
        return ""
    for root, dirs, files in os.walk(in_path):
        for file in files:
            '''筛选tif文件'''
            if not file.split('.')[-1] == 'tif':
                continue
            '''输入路径的文件名'''
            in_file_name = os.path.join(root, file)
            '''创建输出路径文件名'''
            out_file_name = os.path.join(root, os.path.splitext(file)[0] + '_Bit8.tif')
            '''文件存在则删除文件重新生成'''
            if os.path.exists(out_file_name):
                os.remove(out_file_name)
            in_tif = gdal.Open(in_file_name)
            width = in_tif.RasterXSize
            height = in_tif.RasterYSize

            '''跳过8bit'''
            if in_tif.ReadAsArray().dtype.name == 'uint8':
                continue

            geo_transform = in_tif.GetGeoTransform()
            print('左上角坐标 %f %f' % (geo_transform[0], geo_transform[3]))
            print('像素分辨率 %f %f' % (geo_transform[1], geo_transform[5]))
            '''True Color 1,2,3波段'''
            out_tif = gdal.GetDriverByName('GTiff').Create(out_file_name, width, height, in_tif.RasterCount, gdal.GDT_Byte)
            out_tif.SetProjection(in_tif.GetProjection())
            out_tif.SetGeoTransform(geo_transform)

            for i in range(1, int(in_tif.RasterCount) + 1):
                raw_band = in_tif.GetRasterBand(i)
                raw_band_array = raw_band.ReadAsArray()
                band_min = np.min(raw_band_array)
                band_max = np.max(raw_band_array)
                mean = np.mean(raw_band_array)
                std_dev = np.std(raw_band_array, ddof=1)
                # std_dev = np.std(raw_band_array)
                out_band = bit8(raw_band_array, 0, 255, mean, std_dev, 2.5)
                out_tif.GetRasterBand(i).WriteArray(out_band)

            out_tif.FlushCache()
            for i in range(1, int(in_tif.RasterCount) + 1):
                out_tif.GetRasterBand(i).ComputeStatistics(False)
            out_tif.BuildOverviews('average', [2, 4, 8, 16, 32])
            del out_tif
    return out_file_name


if __name__ == '__main__':
    '''调用选择文件夹对话框获取输入路径'''
    in_path = r"D:\Data\hsd\201911\01\YT"

    convert2bit8(in_path)
