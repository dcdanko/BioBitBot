#!/usr/bin/env python

import logging
from pkg_resources import get_distribution

logger = logging.getLogger(__name__)

__version__ = get_distribution("biobitbot").version

from biobitbot.utils import config
from biobitbot.modules.base_module import BaseIBotModule
from biobitbot.analyses.base_analysis import BaseIBotAnalysis

config.version = __version__