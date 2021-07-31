using System;
using System.Collections.Generic;
using System.Linq;
using System.Runtime.InteropServices;
using System.Text;
using System.Threading.Tasks;
using OSGeo.GDAL;
using OSGeo.OGR;
using OSGeo.OSR;

namespace Gdal3.Test
{
    class Program
    {
        private static string GetGB2312(string utf8)
        {
            return Encoding.GetEncoding("gb2312").GetString(Encoding.UTF8.GetBytes(utf8));
        }

        //private static int GetLayerIndexByName();
        //private static int GetFieldIndexByName();

        static void Main(string[] args)
        {
            Gdal.AllRegister();
            Ogr.RegisterAll();
            //Gdal.SetConfigOption("GDAL_DATA",
            //    System.IO.Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "gdal-data"));
            Gdal.SetConfigOption("GDAL_FILENAME_IS_UTF8", "YES");
            Gdal.SetConfigOption("SHAPE_ENCODING", "UTF8");
            Osr.SetPROJSearchPath(System.IO.Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "proj7", "share"));
            //Gdal.SetConfigOption("OGR_SKIP","ODBC");
            //Gdal.SetConfigOption("PGEO_DRIVER_TEMPLATE",
            //    $"DRIVER=Microsoft Access Driver (*.mdb, *.accdb);DBQ=%s");
            //Gdal.SetConfigOption("MDB_DRIVER_TEMPLATE",
            //    $"DRIVER=Microsoft Access Driver (*.mdb, *.accdb);DBQ=%s");

            const string gdbPath = @"C:\Users\x\Documents\ArcGIS\Default.gdb";
            // const string mdbPath = @"C:\Users\x\Documents\ArcGIS\个人.mdb";
            
            var gdbDriver = Ogr.GetDriverByName("FileGDB");
            // var mdbDriver = Ogr.GetDriverByName("PGeo");

            var gdb = gdbDriver.Open(gdbPath, 1);
            var lrCount = gdb.GetLayerCount();
            var lrIndex = -1;
            for (int j = 0; j < lrCount; j++)
            {
                if (gdb.GetLayerByIndex(j).GetName() == GetGB2312("面"))
                {
                    lrIndex = j;
                    break;
                }
            }
            var lr = gdb.GetLayerByIndex(lrIndex);
            var i = lr.FindFieldIndex(GetGB2312("描述"), 1);

            

            // 写入 gdb
            var fn = lr.GetLayerDefn();
            var msIndex = -1;
            for (int j = 0; j < fn.GetFieldCount(); j++)
            {
                if (fn.GetFieldDefn(j).GetName() == GetGB2312("描述"))
                {
                    msIndex = j;
                    break;
                }
            }
            Feature f = new Feature(fn);
            f.SetField(GetGB2312("描述"),"描述内容");
            f.SetField(msIndex, "描述内容");

            lr.CreateFeature(f);

            lr.Dispose();
            //var b = Encoding.UTF8.GetBytes("AB");
            //b = Encoding.GetEncoding("gb2312").GetBytes("景号");
            
        }
    }
}
