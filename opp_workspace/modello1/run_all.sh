#!/bin/bash
#
# Esegue tutti gli 80 run (4 configurazioni x 20 ripetizioni)
#

cd "$(dirname "$0")"
OPPDIR="../omnetpp-6.3.0"

source "$OPPDIR/setenv" -q
export OPP_ENV_VERSION=6
export OMNETPP_ROOT="$(cd $OPPDIR && pwd)"

NEDPATH=".:$OPPDIR/samples/queueinglib"
LIB="$OPPDIR/samples/queueinglib/queueinglib"

# Crea cartella risultati
mkdir -p results

for CONFIG in m05 m10 m14 m20; do
    echo "============================================"
    echo "  Configurazione: $CONFIG (20 run)"
    echo "============================================"
    for RUN in $(seq 0 19); do
        echo -n "  Run #$RUN ... "
        ./modello1 -u Cmdenv -c "$CONFIG" -r "$RUN" \
            -n "$NEDPATH" -l "$LIB" \
            --result-dir=results \
            2>&1 | tail -1
    done
    echo ""
done

echo "Tutti gli 80 run completati. Risultati in: results/"
