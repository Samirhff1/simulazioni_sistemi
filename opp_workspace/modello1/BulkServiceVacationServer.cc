#include "BulkServiceVacationServer.h"
#include "Job.h"

using namespace queueing;

Define_Module(BulkServiceVacationServer);

BulkServiceVacationServer::BulkServiceVacationServer()
    : state(IDLE), batchBeingServed(0),
      endServiceMsg(nullptr), endVacationMsg(nullptr), endSetupMsg(nullptr)
{
}

BulkServiceVacationServer::~BulkServiceVacationServer()
{
    // Elimina jobs rimasti in coda
    while (!queue.isEmpty()) {
        delete queue.pop();
    }
    // Elimina jobs in servizio
    for (auto *job : currentBatch) {
        delete job;
    }
    currentBatch.clear();
    cancelAndDelete(endServiceMsg);
    cancelAndDelete(endVacationMsg);
    cancelAndDelete(endSetupMsg);
}

void BulkServiceVacationServer::initialize()
{
    // Lettura parametri
    a = par("a").intValue();
    b = par("b").intValue();
    sp = par("sp").doubleValue();
    l = par("l").doubleValue();
    u = par("u").doubleValue();

    N = par("N").intValue();
    sv = par("sv").doubleValue();
    z = par("z").doubleValue();
    w = par("w").doubleValue();

    q = par("q").doubleValue();

    // Validazione parametri
    ASSERT(a > 0 && b >= a);
    ASSERT(l >= 0 && u > l);
    ASSERT(N >= a);
    ASSERT(z >= 0 && w > z);
    ASSERT(q > 0);

    // Inizializzazione stato
    state = IDLE;
    batchBeingServed = 0;
    queue.setName("internalQueue");

    // Creazione self-messages
    endServiceMsg = new cMessage("endService");
    endVacationMsg = new cMessage("endVacation");
    endSetupMsg = new cMessage("endSetup");

    // Registrazione segnali
    queueLengthSignal = registerSignal("queueLength");
    numInSystemSignal = registerSignal("numInSystem");
    busySignal = registerSignal("busy");
    serverStateSignal = registerSignal("serverState");
    batchServiceSizeSignal = registerSignal("batchServiceSize");
    serviceTimeSignal = registerSignal("serviceTime");
    vacationDurationSignal = registerSignal("vacationDuration");
    setupDurationSignal = registerSignal("setupDuration");

    // Emissione valori iniziali
    emit(queueLengthSignal, 0);
    emit(numInSystemSignal, 0);
    emit(busySignal, false);
    emit(serverStateSignal, (long)IDLE);

    WATCH(state);
    WATCH(batchBeingServed);
}

void BulkServiceVacationServer::handleMessage(cMessage *msg)
{
    // ============================================
    // Gestione self-messages (fine servizio/vacation/setup)
    // ============================================
    if (msg->isSelfMessage()) {

        if (msg == endServiceMsg) {
            // ----- FINE SERVIZIO -----
            EV << "Service completed for batch of " << batchBeingServed << " jobs." << endl;

            // Invia i job del batch al sink
            for (auto *job : currentBatch) {
                simtime_t svcTime = simTime() - job->getTimestamp();
                job->setTotalServiceTime(job->getTotalServiceTime() + svcTime);
                send(job, "out");
            }
            currentBatch.clear();

            emit(busySignal, false);
            batchBeingServed = 0;
            emit(numInSystemSignal, getSystemPopulation());

            // Controlla se ci sono abbastanza clienti per un nuovo servizio
            int qLen = queue.getLength();
            if (qLen >= a) {
                // Serve immediatamente
                tryStartService();
            }
            else {
                // Single Vacation Rule (SVR):
                // il server va in vacation una singola volta
                startVacation();
            }
        }
        else if (msg == endVacationMsg) {
            // ----- FINE VACATION -----
            simtime_t vacDuration = simTime() - vacationStartTime;
            emit(vacationDurationSignal, vacDuration);
            EV << "Vacation ended. Duration=" << vacDuration
               << " Queue length=" << queue.getLength() << endl;

            int qLen = queue.getLength();
            if (qLen >= N) {
                // N-policy soddisfatta: avvia setup
                startSetup();
            }
            else {
                // SVR: il server rimane dormiente (IDLE) fino a che
                // non si raggiunge N con nuovi arrivi
                state = IDLE;
                emit(serverStateSignal, (long)IDLE);
                EV << "Server goes IDLE (waiting for N=" << N << " customers, current=" << qLen << ")" << endl;
            }
        }
        else if (msg == endSetupMsg) {
            // ----- FINE SETUP -----
            simtime_t setupDur = simTime() - setupStartTime;
            emit(setupDurationSignal, setupDur);
            EV << "Setup completed. Duration=" << setupDur << endl;

            // Dopo il setup, inizia il servizio
            tryStartService();
        }

        return;
    }

    // ============================================
    // Arrivo di un nuovo job dall'esterno
    // ============================================
    Job *job = check_and_cast<Job *>(msg);

    // Segna il tempo di arrivo nella coda
    job->setTimestamp();
    queue.insert(job);
    int qLen = queue.getLength();

    emit(queueLengthSignal, qLen);
    emit(numInSystemSignal, getSystemPopulation());

    EV << "Job " << job->getName() << " arrived. Queue length=" << qLen
       << " State=" << state << endl;

    // Logica di transizione basata sullo stato corrente
    switch (state) {
        case IDLE:
            // Il server è dormiente dopo la vacation.
            // Se raggiungiamo N clienti, avvia setup
            if (qLen >= N) {
                EV << "N-policy threshold reached (" << N << "). Starting setup." << endl;
                startSetup();
            }
            break;

        case VACATION:
            // In vacation: non fare nulla, i clienti si accumulano
            break;

        case SETUP:
            // In fase di setup: non fare nulla, i clienti si accumulano
            break;

        case BUSY:
            // In servizio: non fare nulla, i clienti si accumulano in coda
            break;
    }
}

void BulkServiceVacationServer::tryStartService()
{
    int qLen = queue.getLength();

    if (qLen < a) {
        // Non abbastanza clienti: vai in vacation (SVR) o IDLE
        // Questo caso si verifica solo al primo avvio o dopo setup
        // se nel frattempo la coda è scesa sotto 'a'
        startVacation();
        return;
    }

    // Dimensione del batch: min(qLen, b)
    int r = std::min(qLen, b);

    EV << "Starting bulk service: serving " << r << " jobs (queue had " << qLen << ")" << endl;

    state = BUSY;
    batchBeingServed = r;
    currentBatch.clear();
    emit(serverStateSignal, (long)BUSY);
    emit(busySignal, true);

    // Rimuovi r jobs dalla coda e salvali nel batch corrente
    for (int i = 0; i < r; i++) {
        Job *job = check_and_cast<Job *>(queue.pop());

        // Calcola tempo di attesa in coda per questo job
        simtime_t waitTime = simTime() - job->getTimestamp();
        job->setTotalQueueingTime(job->getTotalQueueingTime() + waitTime);
        job->setQueueCount(job->getQueueCount() + 1);

        // Segna il timestamp per il calcolo del tempo di servizio
        job->setTimestamp();

        currentBatch.push_back(job);
    }

    // Calcola tempo di servizio batch-size-dependent
    simtime_t svcTime = computeServiceTime(r);
    emit(serviceTimeSignal, svcTime);
    emit(batchServiceSizeSignal, r);
    emit(queueLengthSignal, queue.getLength());
    emit(numInSystemSignal, getSystemPopulation());

    EV << "Batch service time = " << svcTime << " for batch size " << r << endl;

    scheduleAt(simTime() + svcTime, endServiceMsg);
}

void BulkServiceVacationServer::startVacation()
{
    int k = queue.getLength();  // numero di clienti in coda (0 <= k < a)
    state = VACATION;
    emit(serverStateSignal, (long)VACATION);
    emit(busySignal, false);

    vacationStartTime = simTime();
    simtime_t vacTime = computeVacationTime(k);

    EV << "Server going on vacation. k=" << k << " vacation time=" << vacTime << endl;

    scheduleAt(simTime() + vacTime, endVacationMsg);
}

void BulkServiceVacationServer::startSetup()
{
    state = SETUP;
    emit(serverStateSignal, (long)SETUP);

    setupStartTime = simTime();
    simtime_t setupTime = computeSetupTime();

    EV << "Server starting setup. Setup time=" << setupTime << endl;

    scheduleAt(simTime() + setupTime, endSetupMsg);
}

simtime_t BulkServiceVacationServer::computeServiceTime(int r)
{
    // t = (r/b)*sp + U(l, u)
    double t1 = ((double)r / (double)b) * sp;
    double t2 = uniform(l, u);
    return t1 + t2;
}

simtime_t BulkServiceVacationServer::computeVacationTime(int k)
{
    // t = ((k+1)/b)*sv + U(z, w)
    double t1 = ((double)(k + 1) / (double)b) * sv;
    double t2 = uniform(z, w);
    return t1 + t2;
}

simtime_t BulkServiceVacationServer::computeSetupTime()
{
    // Distribuzione esponenziale di media q
    return exponential(q);
}

int BulkServiceVacationServer::getSystemPopulation()
{
    return queue.getLength() + batchBeingServed;
}

void BulkServiceVacationServer::refreshDisplay() const
{
    const char *stateStr = "";
    switch (state) {
        case IDLE:     stateStr = "IDLE"; break;
        case VACATION: stateStr = "VACATION"; break;
        case SETUP:    stateStr = "SETUP"; break;
        case BUSY:     stateStr = "BUSY"; break;
    }

    char buf[80];
    snprintf(buf, sizeof(buf), "q=%d %s", queue.getLength(), stateStr);
    getDisplayString().setTagArg("t", 0, buf);

    if (state == BUSY)
        getDisplayString().setTagArg("i2", 0, "status/execute");
    else
        getDisplayString().setTagArg("i2", 0, "");
}

void BulkServiceVacationServer::finish()
{
    EV << "BulkServiceVacationServer: final queue length = " << queue.getLength() << endl;
}
