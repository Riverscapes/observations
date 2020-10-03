import os
import argparse
import psycopg2
from psycopg2.extras import execute_values
from osgeo import ogr
from rscommons import Logger, ProgressBar, dotenv
from rscommons.util import batch


def import_shapefile(shapefile, host, port, user_name, password, database):

    log = Logger('Import')


    conn = psycopg2.connect(user=user_name, password=password, host=host, port=port, database=database)
    curs = conn.cursor()

    driver = ogr.GetDriverByName('ESRI ShapeFile')
    data_source = driver.Open(shapefile)
    layer = data_source.GetLayer()
    total_features = layer.GetFeatureCount()

    # Reach statistics for each reach in our batch
    progbar = ProgressBar(total_features, 50, "Importing features")

    try:
        for feature in layer:
            
            geom_processed += 1
            progbar.update(geom_processed)



        conn.commit()
    except Exception as ex:
        conn.rollback()
        log.error(ex)

    log.info('Shapefile import complete')



def main():
    parser = argparse.ArgumentParser(description='Import point observation ShapeFile into PostGIS'    )
    parser.add_argument('shapefile', help='Point observation ShapeFile path', type=str, default=None)
    parser.add_argument('host', help='Postgres password', type=str)
    parser.add_argument('port', help='Postgres password', type=str)
    parser.add_argument('db', help='Postgres password', type=str)
    parser.add_argument('user_name', help='Postgres user name', type=str)
    parser.add_argument('password', help='Postgres password', type=str)
    parser.add_argument('--verbose', help='(optional) a little extra logging ', action='store_true', default=False)
    args = dotenv.parse_args_env(parser)


    log = Logger('Import')
    log.setup(logPath=os.path.join(os.path.join(os.path.dirname(args.shapefile)), "shapefile_import.log"), verbose=args.verbose)
    log.title('Point Observation ImportTool')

    import_shapefile(args.shapefile, args.host, args.port, args.user_name, args.password, args.db)


if __name__ == '__main__':
    main()
