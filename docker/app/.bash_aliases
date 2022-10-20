glue_container=glue-starter-kit-glue

alias glue="sudo docker exec -it ${glue_container} bash"
alias glue-spark-shell="sudo docker exec -it ${glue_container} /home/glue_user/spark/bin/spark-shell"
alias glue-spark-submit="sudo docker exec -it ${glue_container} /home/glue_user/spark/bin/spark-submit"
alias gluepyspark="sudo docker exec -it ${glue_container} /home/glue_user/spark/bin/pyspark"
alias gluepytest="sudo docker exec -it ${glue_container} /home/glue_user/.local/bin/pytest"
alias start-history-server="sudo docker exec -it ${glue_container} /home/glue_user/spark/sbin/start-history-server.sh"
