using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using OSGeo.GDAL;
using OSGeo.OGR;
using OSGeo.OSR;

namespace Gdal2.Test
{
    class Program
    {
        static void Main(string[] args)
        {
            var e = Encoding.Default;
            Gdal.AllRegister();
            Ogr.RegisterAll();
            //Gdal.SetConfigOption("GDAL_DATA",
            Gdal.SetConfigOption("GDAL_FILENAME_IS_UTF8", "YES");
            Gdal.SetConfigOption("SHAPE_ENCODING", "");

            // 读
            //const string shpFile = @"C:\Users\x\Documents\ArcGIS\镶嵌线.shp";
            //var s = Ogr.Open(shpFile, 0);
            //var lr = s.GetLayerByIndex(0);
            //var fieldName = Encoding.GetEncoding("gb2312").
            //    GetString(Encoding.UTF8.GetBytes("景号"));

            //var index = lr.FindFieldIndex(fieldName, 1);
            //Console.WriteLine(index);
            //s.Dispose();

            // 创建
            const string createdShpFile = @"C:\Users\x\Documents\ArcGIS\黑白像素.shp";
            const string tifFile = @"C:\Users\x\Documents\ArcGIS\dem.tif";

            var tifDs = Gdal.Open(tifFile, Access.GA_ReadOnly);
            
            // 参数为小数，传入0.5取得像素中心点坐标
            var ul = GDALInfoGetPosition(tifDs, 0.0, 0.0);
            Console.WriteLine("  Upper Left (" + ul.Item1 + "," + ul.Item2 + ")");

            // 创建 shp
            var projection = tifDs.GetProjectionRef();
            var srs = new SpatialReference(null);
            if (projection != null)
            {
                if (srs.ImportFromWkt(ref projection) == 0)
                {
                    string wkt;
                    srs.ExportToPrettyWkt(out wkt, 0);
                    Console.WriteLine("Coordinate System is:");
                    Console.WriteLine(wkt);
                }
                else
                {
                    Console.WriteLine("Coordinate System is:");
                    Console.WriteLine(projection);
                }
            }
            
            var drv = Ogr.GetDriverByName("ESRI Shapefile");
            var ds = drv.CreateDataSource(createdShpFile, new string[] { });
            var layer = ds.CreateLayer("黑白像素",srs,wkbGeometryType.wkbPolygon, new string[] { });
            FieldDefn fdefn = new FieldDefn("中文字段", FieldType.OFTString);

            fdefn.SetWidth(128);

            if (layer.CreateField(fdefn, 1) != 0)
            {
                Console.WriteLine("Creating Name field failed.");
            }

            layer.Dispose();
            tifDs.Dispose();

            //const string mdbPath = @"C:\Users\x\Documents\ArcGIS\个人一.mdb";

            //var mdb = Ogr.Open(mdbPath, 0);
            //var lr2 = mdb.GetLayerByName("面");
            //var j = lr2.FindFieldIndex("描述", 1);
            //Feature f;
            //while ((f = lr2.GetNextFeature()) != null)
            //{
            //    var value = f.GetFieldAsString(j);
            //    Console.WriteLine(value);
            //}
        }

        private static Tuple<double,double> GDALInfoGetPosition(Dataset ds, double x, double y)
        {
            var adfGeoTransform = new double[6];
            ds.GetGeoTransform(adfGeoTransform);

            var dfGeoX = adfGeoTransform[0] + adfGeoTransform[1] * x + adfGeoTransform[2] * y;
            var dfGeoY = adfGeoTransform[3] + adfGeoTransform[4] * x + adfGeoTransform[5] * y;

            return Tuple.Create(dfGeoX, dfGeoY);
        }
    }
}
