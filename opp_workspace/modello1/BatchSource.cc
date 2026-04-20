#include "BatchSource.h"
#include "Job.h"

using namespace queueing;

Define_Module(BatchSource);

BatchSource::~BatchSource()
{
    cancelAndDelete(timerMsg);
}

void BatchSource::initialize()
{
    jobCounter = 0;
    createdSignal = registerSignal("created");
    batchSizeSignal = registerSignal("batchSize");
    WATCH(jobCounter);

    m = par("m").doubleValue();
    x1 = par("x1").intValue();
    x2 = par("x2").intValue();

    startTime = par("startTime").doubleValue();
    stopTime = par("stopTime").doubleValue();

    timerMsg = new cMessage("batchTimer");
    scheduleAt(startTime, timerMsg);
}

void BatchSource::handleMessage(cMessage *msg)
{
    ASSERT(msg->isSelfMessage());

    if (stopTime >= 0 && simTime() >= stopTime) {
        return;
    }

    // Determina dimensione del batch: uniforme discreta in [x1, x2]
    int batchSize = intuniform(x1, x2);
    emit(batchSizeSignal, batchSize);

    EV << "Generating batch of " << batchSize << " jobs at t=" << simTime() << endl;

    // Genera e invia singoli job (il server si occuperà di accumularli)
    for (int i = 0; i < batchSize; i++) {
        char buf[80];
        snprintf(buf, sizeof(buf), "job-%d", ++jobCounter);
        Job *job = new Job(buf);
        job->setTimestamp();  // marca il tempo di arrivo nel sistema
        send(job, "out");
    }

    emit(createdSignal, batchSize);

    // Prossimo arrivo: tempo inter-arrivo esponenziale di media m
    simtime_t nextArrival = exponential(m);
    scheduleAt(simTime() + nextArrival, timerMsg);
}

void BatchSource::finish()
{
    EV << "BatchSource: total jobs created = " << jobCounter << endl;
}
