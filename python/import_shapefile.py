import os
import json
import argparse
import psycopg2
import getpass
import datetime
from psycopg2.extras import execute_values
from osgeo import ogr
from rscommons import Logger, ProgressBar, dotenv
from rscommons.util import batch
from rscommons.shapefile import get_transform_from_epsg


def import_shapefile(shapefile, host, port, user_name, password, database):

    log = Logger('Import')


    conn = psycopg2.connect(user=user_name, password=password, host=host, port=port, database=database)
    curs = conn.cursor()

    driver = ogr.GetDriverByName('ESRI ShapeFile')
    data_source = driver.Open(shapefile)
    layer = data_source.GetLayer()
    total_features = layer.GetFeatureCount()
    _spatial_ref, transform = get_transform_from_epsg( layer.GetSpatialRef(), 4326)

    curs.execute('INSERT INTO uploads (added_by, file_name, remarks) VALUES (%s, %s, %s) RETURNING id', 
        [getpass.getuser(), os.path.basename(shapefile), 'Python Script Import'])
    upload_id = curs.fetchone()[0]

    curs.execute('SELECT name, id FROM observation_types')
    obs_types = {row[0].replace('Dam', '').replace(' ', '').lower(): row[1] for row in curs.fetchall()}

    certainties = {'Low': 1, 'Medium': 2, 'High': 3}

    # Reach statistics for each reach in our batch
    progbar = ProgressBar(total_features, 50, "Importing features")

    try:
        observations = []
        for feature in layer:
            geom = feature.GetGeometryRef()
            geom.Transform(transform)
            geom.FlattenTo2D()

            metadata = {field: feature.GetField(field) for field in [
                'Feature_Ty', 'Certainty', 'Year', 'Dam_Type', 'CreationDa', 
                'Creator', 'EditDate', 'Editor', 'Snapped', 'Imagery_Ye'] }

            # print(metadata)

            clean_type = feature.GetField('Feature_Ty').replace('_', '').replace('Dam', '').lower() if feature.GetField('Feature_Ty') else 'Unknown'.lower()
            obs_date = datetime.datetime.strptime(feature.GetField('CreationDa'), '%Y/%m/%d')
            year = int(feature.GetField('Year')) if feature.GetField('Year') else None
            certainty = certainties[feature.GetField('Certainty')] if feature.GetField('Certainty') in certainties else 0

            observations.append((
                upload_id,
                geom.ExportToWkb(),
                obs_date,
                feature.GetField('Creator'),
                year,
                obs_types[clean_type],
                True,
                certainty,
                json.dumps(metadata)
            ))
            
            progbar.update(len(observations))

        progbar.finish()

        curs.executemany("""
            INSERT INTO observations (
                upload_id,
                geom,
                obs_date,
                observer,
                obs_year,
                obs_type_id,
                is_public,
                confidence,
                metadata
            ) VALUES (%s, ST_GeomFromWKB(%s, 4326), %s, %s, %s, %s, %s, %s, %s)""", observations)
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
