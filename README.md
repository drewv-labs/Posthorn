# JobSeek
Automated job post scanner and alerting with posting specific cover letter generation. 


example usage:

```py
import posthorn
import posthorn.adapters as adapters

alerting_carrier = adapters.TelegramCarrier.from_config(adapters.TelegramConfig(
    bot_token='123',
    chat_id='abc'
))

job_boards = posthorn.JobBoardManager.from_config(posthorn.JobBoardManagerConfig(
    ...
))

daemon = posthorn.Daemon(
    alerting_carrier=alerting_carrier,
    job_boards=job_boards,
    state=StateMachine
)

daemon.start()

```
