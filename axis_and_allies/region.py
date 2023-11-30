import logging

import numpy
import pandas

import axis_and_allies.setup_logger as setup_logger

logger = logging.getLogger(setup_logger.LOGGER_NAME)

REGION_TYPE_LAND = "land"
REGION_TYPE_WATER = "water"

class Region:
    def __init__(self, id=None, name=None, region_type=None, adjacent_regions=[], ipc_production=None,
                 has_industry=False, unit_list=[]):
        self.id = id
        self.name = name
        self.region_type = region_type
        self.adjacent_regions = list(adjacent_regions)
        self.ipc_production = ipc_production
        self.has_industry = has_industry
        self.unit_list = unit_list
    
    def __str__(self) -> str:
        return """name:  {}
id:  {}
region_type:  {}
adjacent_regions:  {}
ipc_production:  {}
has_industry:  {}
unit_list:  {}""".format(
            self.name, self.id, self.region_type, 
            [(x.id, x.name) for x in self.adjacent_regions],
            self.ipc_production, self.has_industry,
            [(x.id, x.name) for x in self.unit_list])

    def __repr__(self) -> str:
        return self.__str__()

    def copy(self):
        my_copy = Region(id=self.id, name=self.name, region_type=self.region_type, adjacent_regions=self.adjacent_regions,
                         ipc_production=self.ipc_production, unit_list=list(self.unit_list))
        my_copy.id = self.id
        return my_copy
    
    def get_adjacent_region_ids(self):
        return [x.id for x in self.adjacent_regions]
    

def load_from_txt(input_file):
    data_df = pandas.read_csv(input_file, sep="\t", index_col=0)
    logger.debug("data_df:\n{}".format(data_df))

    assert data_df.region_type.isin({REGION_TYPE_LAND, REGION_TYPE_WATER}).all()
    logger.debug("data_df.ipc_production.dtype:  {}".format(data_df.ipc_production.dtype))
    assert data_df.ipc_production.dtype == numpy.int64
    logger.debug("data_df.has_industry.dtype:  {}".format(data_df.has_industry.dtype))
    assert data_df.has_industry.dtype == numpy.bool_

    region_dict = {}
    for id in data_df.index:
        cur_row = data_df.loc[id]
        cur_region = Region(
            id=id,
            name=cur_row["name"],
            region_type=cur_row["region_type"],
            ipc_production=cur_row["ipc_production"],
            has_industry=cur_row["has_industry"]
        )

        assert not id in region_dict
        region_dict[id] = cur_region

    logger.debug("region_dict.keys():  {}".format(region_dict.keys()))

    for id in data_df.index:
        cur_region = region_dict[id]
        logger.debug("id:  {}  cur_region.name:  {}".format(id, cur_region.name))

        adjacent_region_ids = [int(x) for x in data_df.loc[id, "adjacent_region_ids"].split(",")]
        logger.debug("adjacent_region_ids:  {}".format(adjacent_region_ids))

        cur_region.adjacent_regions = [region_dict[x] for x in adjacent_region_ids]

    validate_region_connections(region_dict)

    return region_dict

def validate_region_connections(region_dict):
    mismatch_list = []
    for cur_region in region_dict.values():
        for cur_adj_region in cur_region.adjacent_regions:
            if not cur_region.id in cur_adj_region.get_adjacent_region_ids():
                mismatch_list.append((cur_region, cur_adj_region))
    
    if len(mismatch_list) > 0:
        logger.error("mismatching region connections found:")
        for cur_region, cur_adj_region in mismatch_list:
            logger.debug("cur_region:  {} {}  cur_adj_region:  {} {}".format(
                cur_region.id, cur_region.name, cur_adj_region.id, cur_adj_region.name
            ))
        raise AxisAndAlliesRegionMismatchConnectionsException()


class AxisAndAlliesRegionMismatchConnectionsException(Exception):
    pass