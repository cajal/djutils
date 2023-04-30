import datajoint as dj


def foreigns(tables, schema):
    """
    Parameters
    ----------
    tables : Sequence[type(dj.UserTable)]
        tables to be referenced

    schema : dj.Schema
        schema that houses the referencing table

    Returns
    -------
    list[str]:
        list of foreign keys
    dict[str, type(dj.UserTable) | dj.VirtualModule]
        context for schema call
    """
    context = dict()
    foreigns = []

    for table in tables:

        database = table.database

        if database == schema.database:

            if issubclass(table, dj.Part):
                foreign = f"{table._master.__name__}.{table.__name__}"
                context[table._master.__name__] = table._master
            else:
                foreign = table.__name__
                context[table.__name__] = table

        else:
            if issubclass(table, dj.Part):
                foreign = f"{database}.{table._master.__name__}.{table.__name__}"
            else:
                foreign = f"{database}.{table.__name__}"

            if database not in context:
                context[database] = dj.create_virtual_module(database, database)

        assert foreign not in foreigns
        foreigns.append(foreign)

    return foreigns, context
