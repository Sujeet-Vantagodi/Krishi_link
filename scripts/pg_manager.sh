#!/bin/bash
PGDATA="/home/sujeet/pgdata"
PG_BIN="/usr/lib/postgresql/18/bin"

case "$1" in
  start)
    if $PG_BIN/pg_ctl -D "$PGDATA" status > /dev/null 2>&1; then
      echo "PostgreSQL is already running."
    else
      $PG_BIN/pg_ctl -D "$PGDATA" -l "$PGDATA/logfile" start
      echo "PostgreSQL started on 0.0.0.0:5432."
    fi
    ;;
  stop)
    $PG_BIN/pg_ctl -D "$PGDATA" stop
    ;;
  restart)
    $PG_BIN/pg_ctl -D "$PGDATA" -l "$PGDATA/logfile" restart
    ;;
  status)
    $PG_BIN/pg_ctl -D "$PGDATA" status
    ;;
  *)
    echo "Usage: $0 {start|stop|restart|status}"
    exit 1
    ;;
esac
