import psycopg2


def project_details(accountid, secret):
    postgresPassword = secret.get('postgresPassword')
    postgresHost = 'azr-projectname-replica.postgres.database.azure.com'
    postgresUser = 'projectname@' + postgresHost.split('.')[0]
    postgresDbName = "postgres"
    postgresSSLmode = 'require'
    postgresConnString = f'host={postgresHost} user={postgresUser} dbname={postgresDbName} password={postgresPassword} sslmode={postgresSSLmode} '
    postgresTable = 'aws_accounts'
    postgresConn = psycopg2.connect(postgresConnString)
    postgresCursor = postgresConn.cursor()
    postgresSQL = f'SELECT * FROM {postgresTable} where cloud_id = \'{accountid}\';'
    postgresCursor.execute(postgresSQL)
    rows = postgresCursor.fetchall()
    if rows:
        name, lob, environment = rows[0][1], rows[0][2], rows[0][3]
        postgresCursor.close()
        postgresConn.close()
        return name, lob, environment
    postgresCursor.close()
    postgresConn.close()
    return "None", "None", "None"
