"""
配置管理模块
==========

为AI记账系统提供统一的配置管理功能，支持多种配置源和验证。
"""

import os
import json
import logging
# import jsonschema # No longer needed as ConfigManager is removed
from pathlib import Path
from typing import Dict, Any, Optional, List, Union
# import copy # No longer needed

# 导入异常 (ConfigError, ConfigLoadError, ConfigValidationError might still be useful if other parts of common use them)
from core.common.exceptions import ConfigError, ConfigLoadError, ConfigValidationError

# 配置日志
logger = logging.getLogger(__name__) # Changed from 'config_manager'

# ConfigManager class and its methods are removed.

# The get_config_manager function is removed as it's no longer needed.
# If there's a need to signal deprecation for a while, it could be kept with a warning,
# but since all call sites are intended to be updated, direct removal is cleaner.

# The _config_manager global variable is also removed.

# __all__ will be updated to only export relevant exceptions if they are used by other modules.
# For now, assuming they are still needed.
__all__ = ['ConfigError', 'ConfigLoadError', 'ConfigValidationError']