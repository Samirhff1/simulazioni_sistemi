#ifndef __BULKSERVICEVACATIONSERVER_H
#define __BULKSERVICEVACATIONSERVER_H

#include <omnetpp.h>
#include <vector>

namespace queueing { class Job; }

using namespace omnetpp;
using queueing::Job;

/**
 * BulkServiceVacationServer: implementa un server con:
 *  - Coda interna (buffer infinito)
 *  - Bulk service con regola (a, b): serve minimo 'a' e massimo 'b' clienti
 *  - Tempo di servizio batch-size-dependent: t = (r/b)*sp + U(l, u)
 *  - Single Vacation Rule (SVR) con durata queue-length-dependent
 *  - N-policy: il server si risveglia quando ci sono N clienti in coda
 *  - Set-up time: esponenziale di media q
 *
 * Stati del server:
 *  IDLE        - in attesa (dopo vacation, meno di N clienti in coda)
 *  VACATION    - in vacation
 *  SETUP       - in fase di setup (dopo risveglio da vacation/idle con N clienti)
 *  BUSY        - in servizio
 */
class BulkServiceVacationServer : public cSimpleModule
{
  public:
    enum ServerState {
        IDLE,
        VACATION,
        SETUP,
        BUSY
    };

  private:
    // Stato
    ServerState state;
    cQueue queue;              // coda interna
    int batchBeingServed;      // dimensione del batch attualmente in servizio
    std::vector<Job *> currentBatch;  // jobs attualmente in servizio

    // Self-messages
    cMessage *endServiceMsg;
    cMessage *endVacationMsg;
    cMessage *endSetupMsg;

    // Parametri modello
    int a;       // soglia minima per servizio
    int b;       // capacità massima batch di servizio
    double sp;   // parametro tempo servizio deterministico
    double l;    // limite inferiore U(l,u) servizio
    double u;    // limite superiore U(l,u) servizio

    int N;       // soglia N-policy
    double sv;   // parametro tempo vacation deterministico
    double z;    // limite inferiore U(z,w) vacation
    double w;    // limite superiore U(z,w) vacation

    double q;    // media tempo setup (esponenziale)

    // Statistiche
    simsignal_t queueLengthSignal;
    simsignal_t numInSystemSignal;
    simsignal_t busySignal;
    simsignal_t serverStateSignal;
    simsignal_t batchServiceSizeSignal;
    simsignal_t serviceTimeSignal;
    simsignal_t vacationDurationSignal;
    simsignal_t setupDurationSignal;

    // Timestamp per calcolo durata vacation
    simtime_t vacationStartTime;
    simtime_t setupStartTime;

    // Metodi interni
    void tryStartService();
    void startVacation();
    void startSetup();
    simtime_t computeServiceTime(int r);
    simtime_t computeVacationTime(int k);
    simtime_t computeSetupTime();
    int getSystemPopulation();

  protected:
    virtual void initialize() override;
    virtual void handleMessage(cMessage *msg) override;
    virtual void refreshDisplay() const override;
    virtual void finish() override;

  public:
    BulkServiceVacationServer();
    virtual ~BulkServiceVacationServer();
};

#endif
