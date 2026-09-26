# Posthorn Adapters

## Adapter Requirements:  
Each `AlertingCarrier` & `JobBoard` adapter file will contain: 
  - config model (data class) 
  - adapter class definition

Update `__init__.py` to include the adapter.
e.g., 
```py
from .linkedin import LinkedIn, LinkedInConfig
from .telegram import Telegram, TelegramConfig
```
