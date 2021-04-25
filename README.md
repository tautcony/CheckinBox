# CheckinBox

1. 点击项目右上角的Fork，Fork此项目
2. 到自己Fork的项目点击`Actions`，如果未启用，需要手动启用，然后启用需要运行的Workflows
3. 到自己Fork的项目点击`Setting`→`Secrets`→`New secrets`
4. 填写`Name`，和`Value`，具体到各脚本中看
5. 在`Actions`中的`run`下点击`Run workflow`即可手动执行签到，后续运行按照schedule，默认在每天凌晨0:30自动签到，可自行修改
