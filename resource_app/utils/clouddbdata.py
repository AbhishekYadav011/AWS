import psycopg2


def project_details(accountid, secret):
    postgresPassword = secret.get('postgresPassword')
    postgresHost = 'azr-projectname-replica.postgres.database.azure.com'
    postgresUser = 'projectname@' + postgresHost.split('.')[0]
    postgresDbName = "postgres"
    postgresSSLmode = 'require'
    postgresConnString = "host={0} user={1} dbname={2} password={3} sslmode={4}".format(postgresHost, postgresUser,
                                                                                        postgresDbName,
                                                                                        postgresPassword,
                                                                                        postgresSSLmode)
    postgresTable = 'aws_accounts'
    postgresConn = psycopg2.connect(postgresConnString)
    postgresCursor = postgresConn.cursor()
    postgresSQL = "SELECT * FROM %s where cloud_id = '%s';" % (postgresTable, accountid)
    postgresCursor.execute(postgresSQL)
    rows = postgresCursor.fetchall()
    if rows:
        name, lob, environment = rows[0][1], rows[0][2], rows[0][3]
        postgresCursor.close()
        postgresConn.close()
        return name, lob, environment
    else:
        name, lob, environment = "None", "None", "None"
        postgresCursor.close()
        postgresConn.close()
        return name, lob, environment
