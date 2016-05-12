#!/usr/bin/env python

import logging
from pkg_resources import get_distribution

logger = logging.getLogger(__name__)

__version__ = get_distribution("ibot").version

from ibot.utils import config
from ibot.modules.base_module import BaseIBotModule
from ibot.analyses.base_analysis import BaseIBotAnalysis

config.version = __version__