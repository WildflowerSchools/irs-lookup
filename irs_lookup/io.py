import os
import pickle

from .log import logger


def write_dataframe(df, filename, format='csv', directory='.'):
    filename = "{}.{}".format(filename, format)
    path = os.path.join(
        directory,
        filename
    )

    logger.info("Writing '{}' record to {}".format(filename, path))

    if format == 'csv':
        df.to_csv(path, index=False)
    elif format == 'pickle':
        with open(path, 'wb') as fp:
            pickle.dump(df, fp)
