#!/bin/bash


for node in 1 # 2 4 8 16
do
    tasks=$((node * 32 * 2))
    LOG="test_log.parsl.${node}nodes.${tasks}tasks.32workers.log"
    echo "Starting test with workers=$((node * 32))" &>> $LOG
    python3 test.py --workers_per_node=32 --nodes=$node --count=$tasks &>> $LOG

    LOG="test_log.redis.${node}nodes.${tasks}tasks.32workers.log"
    echo "Starting test with workers=$((node * 32))" &>> $LOG
    python3 test.py --workers_per_node=32 --nodes=$node --count=$tasks --store redis &>> $LOG

    #LOG="test_log.file.${node}nodes.${tasks}tasks.32workers.log"
    #echo "Starting test with workers=$((node * 32))" &>> $LOG
    #python3 test.py --workers_per_node=32 --nodes=$node --count=$tasks --store file &>> $LOG

    #LOG="test_log.margo.${node}nodes.${tasks}tasks.32workers.log"
    #echo "Starting test with workers=$((node * 32))" &>> $LOG
    #python3 test.py --workers_per_node=32 --nodes=$node --count=$tasks --store margo &>> $LOG
done
