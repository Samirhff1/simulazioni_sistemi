//
// Modello di simulazione: Bulk Service Vacation Queue con N-policy
//
// Riferimento: P. Karan, S. Pradhan, "Analysis of a queue-length-dependent
// vacation queue with bulk service, N-policy, set-up time and cost optimization"
// Performance Evaluation 167 (2025)
//
// Variante con:
// - Arrivi batch (compound Poisson)
// - Bulk service (a, b)
// - Service time batch-size-dependent
// - Single Vacation Rule (SVR), queue-length-dependent
// - N-policy
// - Set-up time esponenziale
//

import ned.IdealChannel;
import org.omnetpp.queueing.Sink;


// ==========================================================================
// BatchSource: sorgente con arrivi batch (compound Poisson)
// - Tempo inter-arrivo: esponenziale di media m
// - Dimensione batch X: uniforme discreta in [x1, x2]
// ==========================================================================
simple BatchSource
{
    parameters:
        double m;                                    // media tempo inter-arrivo (esponenziale)
        int x1;                                      // dimensione minima batch
        int x2;                                      // dimensione massima batch
        double startTime @unit(s) = default(0s);     // tempo di inizio generazione
        double stopTime @unit(s) = default(-1s);     // tempo di stop (-1 = mai)

        @signal[created](type=long);
        @signal[batchSize](type=long);
        @statistic[created](title="jobs created"; record=sum,vector;
                    interpolationmode=none);
        @statistic[batchSize](title="batch size"; record=mean,histogram,vector; interpolationmode=none);

        @display("i=block/source");
    gates:
        output out;
}


// ==========================================================================
// BulkServiceVacationServer: server con coda interna, bulk service (a,b),
// vacation SVR queue-length-dependent, N-policy, set-up time
// ==========================================================================
simple BulkServiceVacationServer
{
    parameters:
        // Bulk service parameters
        int a;           // soglia minima per avviare il servizio
        int b;           // capacità massima batch di servizio

        // Service time: t = (r/b)*sp + U(l, u)
        double sp;       // parametro deterministico
        double l;        // limite inferiore uniforme
        double u;        // limite superiore uniforme

        // N-policy
        int N;           // soglia di riattivazione del server

        // Vacation time (SVR): t = ((k+1)/b)*sv + U(z, w)
        double sv;       // parametro deterministico vacation
        double z;        // limite inferiore uniforme vacation
        double w;        // limite superiore uniforme vacation

        // Setup time: esponenziale di media q
        double q;        // media setup time

        // Segnali e statistiche
        @signal[queueLength](type=long);
        @signal[numInSystem](type=long);
        @signal[busy](type=bool);
        @signal[serverState](type=long);
        @signal[batchServiceSize](type=long);
        @signal[serviceTime](type=simtime_t);
        @signal[vacationDuration](type=simtime_t);
        @signal[setupDuration](type=simtime_t);

        @statistic[queueLength](title="queue length"; record=timeavg,max,vector; interpolationmode=sample-hold);
        @statistic[numInSystem](title="number in system"; record=timeavg,max,vector; interpolationmode=sample-hold);
        @statistic[busy](title="server busy"; record=timeavg,vector; interpolationmode=sample-hold);
        @statistic[serverState](title="server state"; record=vector; interpolationmode=sample-hold);
        @statistic[batchServiceSize](title="batch service size"; record=mean,histogram,vector; interpolationmode=none);
        @statistic[serviceTime](title="service time"; record=mean,histogram,vector; interpolationmode=none);
        @statistic[vacationDuration](title="vacation duration"; record=mean,histogram,vector; interpolationmode=none);
        @statistic[setupDuration](title="setup duration"; record=mean,vector; interpolationmode=none);

        @display("i=block/server;q=internalQueue");
    gates:
        input in[];
        output out;
}


// ==========================================================================
// Rete del modello
// ==========================================================================
network Modello_progetto
{
    @display("bgb=600,300");
    submodules:
        source: BatchSource {
            @display("p=50,150");
        }
        server: BulkServiceVacationServer {
            @display("p=300,150");
        }
        sink: Sink {
            @display("p=550,150");
        }
    connections:
        source.out --> IdealChannel --> server.in++;
        server.out --> IdealChannel --> sink.in++;
}

