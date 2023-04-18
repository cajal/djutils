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
        name = table.__name__
        database = table.database

        if database == schema.database:
            foreign = name
            context[name] = table
        else:
            foreign = f"{database}.{name}"
            if database not in context:
                context[database] = dj.create_virtual_module(database, database)

        assert foreign not in foreigns
        foreigns.append(foreign)

    return foreigns, context
