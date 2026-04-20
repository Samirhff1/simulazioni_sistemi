#ifndef __BATCHSOURCE_H
#define __BATCHSOURCE_H

#include <omnetpp.h>

using namespace omnetpp;

/**
 * BatchSource: genera arrivi batch secondo un processo di Poisson composto.
 * - Tempo inter-arrivo: esponenziale di media m
 * - Dimensione batch X: uniforme discreta in [x1, x2]
 */
class BatchSource : public cSimpleModule
{
  private:
    int jobCounter;
    simtime_t startTime;
    simtime_t stopTime;
    cMessage *timerMsg;

    // Parametri
    double m;     // media inter-arrivo
    int x1, x2;  // range dimensione batch

    // Segnali statistici
    simsignal_t createdSignal;
    simsignal_t batchSizeSignal;

  protected:
    virtual void initialize() override;
    virtual void handleMessage(cMessage *msg) override;
    virtual void finish() override;

  public:
    BatchSource() : timerMsg(nullptr) {}
    virtual ~BatchSource();
};

#endif
