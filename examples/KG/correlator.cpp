#include "correlator.h"
#include <math.h>

namespace {

constexpr double kUnusedCorrelatorSample = -2.0e10;

inline bool hasStoredSample(const double value) {
	return value > -1.0e10;
}

} // namespace

/////////////////////////////////////////
// Correlator class
/////////////////////////////////////////
Correlator::Correlator(const unsigned int numcorrin, const unsigned int pin, const unsigned int min) {
	setsize(numcorrin, pin, min);
}


Correlator::~Correlator() {

	if (numcorrelators == 0) return;

	delete[] shift;
	delete[] correlation;
	delete[] ncorrelation;
	delete[] accumulator;
	delete[] naccumulator;
	delete[] insertindex;

	delete[] t;
	delete[] f;
	delete[] tav;
	delete[] fav;
}


void Correlator::setsize(const unsigned int numcorrin, const unsigned int pin, const unsigned int min) {
	numcorrelators = numcorrin;
	p = pin;
	m = min;
	dmin = p / m;

	/* It can be optimized to
	   length = p + (numcorrelators-1)*(p-p/m)
	   = p*(numcorrelators - (numcorrelators-1)/m)) */
	length = numcorrelators*p;

	shift = new double*[numcorrelators];
	correlation = new double*[numcorrelators];
	ncorrelation = new unsigned long int*[numcorrelators];
	accumulator = new double[numcorrelators];
	naccumulator = new unsigned int[numcorrelators];
	insertindex = new unsigned int[numcorrelators];

	for (unsigned int j = 0; j < numcorrelators; ++j) {
		shift[j] = new double[p];

		/* It can be optimized: Apart from correlator 0, correlation and ncorrelation arrays only use p/2 values */
		correlation[j] = new double[p];
		ncorrelation[j] = new unsigned long int[p];
	}

	t = new double[length];
	f = new double[length];
	tav = new double[length];
	fav = new double[length];
}


void Correlator::initialize() {
	resetCurrentState();
	resetAverageState();
}

void Correlator::resetCurrentState() {
	for (unsigned int j = 0; j < numcorrelators; ++j) {
		for (unsigned int i = 0; i < p; ++i) {
			shift[j][i] = kUnusedCorrelatorSample;
			correlation[j][i] = 0;
			ncorrelation[j][i] = 0;
		}
		accumulator[j] = 0.0;
		naccumulator[j] = 0;
		insertindex[j] = 0;
	}

	for (unsigned int i = 0; i < length; ++i) {
		t[i] = 0;
		f[i] = 0;
	}

	npcorr = 0;
	kmax = 0;
}

void Correlator::resetAverageState() {
	for (unsigned int i = 0; i < length; ++i) {
		tav[i] = 0;
		fav[i] = 0;
	}

	npcorrmax = 0;
	nexp = 0;
}

void Correlator::add(const double w, const unsigned int k) {

	/// Samples that would fall beyond the last multi-tau level are dropped.
	if (k == numcorrelators) return;
	if (k > kmax) kmax = k;

	/// Insert the new sample at the current ring-buffer cursor.
	shift[k][insertindex[k]] = w;

	/// Every m samples we forward the block average to the next coarser level.
	accumulator[k] += w;
	++naccumulator[k];
	if (naccumulator[k] == m) {
		add(accumulator[k] / m, k + 1);
		accumulator[k] = 0;
		naccumulator[k] = 0;
	}

	/// The finest level stores every lag. Coarser levels skip the overlapping
	/// short-time region already covered by finer levels.
	unsigned int ind1 = insertindex[k];
	if (k == 0) {
		int ind2 = ind1;
		for (unsigned int j = 0; j < p; ++j) {
			if (hasStoredSample(shift[k][ind2])) {
				correlation[k][j] += shift[k][ind1] * shift[k][ind2];
				++ncorrelation[k][j];
			}
			--ind2;
			if (ind2 < 0) ind2 += p;
		}
	}
	else {
		int ind2 = ind1 - dmin;
		for (unsigned int j = dmin; j < p; ++j) {
			if (ind2 < 0) ind2 += p;
			if (hasStoredSample(shift[k][ind2])) {
				correlation[k][j] += shift[k][ind1] * shift[k][ind2];
				++ncorrelation[k][j];
			}
			--ind2;
		}
	}

	++insertindex[k];
	if (insertindex[k] == p) insertindex[k] = 0;
}

void Correlator::evaluate() {
	unsigned int im = 0;

	// First correlator
	for (unsigned int i = 0; i < p; ++i) {
		if (ncorrelation[0][i] > 0) {
			t[im] = i;
			f[im] = correlation[0][i] / ncorrelation[0][i];
			++im;
		}
	}

	// Subsequent correlators
	for (unsigned int k = 1; k < kmax; ++k) {
		for (unsigned int i = dmin; i < p; ++i) {
			if (ncorrelation[k][i] > 0) {
				t[im] = i * pow((double)m, k);
				f[im] = correlation[k][i] / ncorrelation[k][i];
				++im;
			}
		}
	}

	npcorr = im;
}

void Correlator::toaverage() {
	for (unsigned int i = 0; i < npcorr; ++i) {
		fav[i] += f[i];
		tav[i] = t[i];
	}
	if (npcorr > npcorrmax)
		npcorrmax = npcorr;
	++nexp;
}


void Correlator::clear() {
	resetCurrentState();
}

void Correlator::save(FILE *fout) {
	fprintf(fout, "%d %d %d %d %d ", numcorrelators, p, m, dmin, length);
	fprintf(fout, "%d %d %d %d ", npcorr, npcorrmax, nexp, kmax);
	for (unsigned int i = 0; i < p; ++i)
		for (unsigned int j = 0; j <= kmax; ++j)
			fprintf(fout, "%lg %lg %ld ", shift[j][i], correlation[j][i], ncorrelation[j][i]);
	for (unsigned int i = 0; i < kmax; ++i)
		fprintf(fout, "%lg %d %d ", accumulator[i], naccumulator[i], insertindex[i]);
	for (unsigned int i = 0; i < npcorr; ++i)
		fprintf(fout, "%lg %lg ", t[i], f[i]);
	for (unsigned int i = 0; i < npcorrmax; ++i)
		fprintf(fout, "%lg %lg ", tav[i], fav[i]);
}

void Correlator::read(FILE *fin) {
	fscanf(fin, "%d %d %d %d %d", &numcorrelators, &p, &m, &dmin, &length);
	setsize(numcorrelators, p, m);
	initialize();
	fscanf(fin, "%d %d %d %d", &npcorr, &npcorrmax, &nexp, &kmax);
	for (unsigned int i = 0; i < p; ++i)
		for (unsigned int j = 0; j <= kmax; ++j)
			fscanf(fin, "%lg %lg %ld", &shift[j][i], &correlation[j][i], &ncorrelation[j][i]);
	for (unsigned int i = 0; i < kmax; ++i)
		fscanf(fin, "%lg %d %d", &accumulator[i], &naccumulator[i], &insertindex[i]);
	for (unsigned int i = 0; i < npcorr; ++i)
		fscanf(fin, "%lg %lg", &t[i], &f[i]);
	for (unsigned int i = 0; i < npcorrmax; ++i)
		fscanf(fin, "%lg %lg", &tav[i], &fav[i]);
}

/////////////////////////////////////////
// CrossCorrelator class
/////////////////////////////////////////
CrossCorrelator::CrossCorrelator(const unsigned int numcorrin, const unsigned int pin, const unsigned int min) {
	setsize(numcorrin, pin, min);
}


void CrossCorrelator::setsize(const unsigned int numcorrin, const unsigned int pin, const unsigned int min) {

	Correlator::setsize(numcorrin, pin, min);
	shift2 = new double*[numcorrelators];
	accumulator2 = new double[numcorrelators];

	for (unsigned int j = 0; j < numcorrelators; ++j)
		shift2[j] = new double[p];
}

CrossCorrelator::~CrossCorrelator() {
	if (numcorrelators == 0) return;
	delete[] shift2;
	delete[] accumulator2;
}

void CrossCorrelator::initialize() {
	Correlator::initialize();

	for (unsigned int j = 0; j < numcorrelators; ++j)
		accumulator2[j] = 0.0;
}

void CrossCorrelator::add(const double wA, const double wB, const unsigned int k) {
	/// Samples that would fall beyond the last multi-tau level are dropped.
	if (k == numcorrelators) return;
	if (k > kmax) kmax = k;

	/// Insert the new sample pair at the current ring-buffer cursor.
	shift[k][insertindex[k]] = wA;
	shift2[k][insertindex[k]] = wB;

	/// Every m samples we forward the block average to the next coarser level.
	accumulator[k] += wA;
	accumulator2[k] += wB;
	++naccumulator[k];
	if (naccumulator[k] == m) {
		add(accumulator[k] / m, accumulator2[k] / m, k + 1);
		accumulator[k] = 0;
		accumulator2[k] = 0;
		naccumulator[k] = 0;
	}

	/// The finest level stores every lag. Coarser levels start at dmin so the
	/// short-time window is not duplicated across levels.
	unsigned int ind1 = insertindex[k];
	if (k == 0) {
		int ind2 = ind1;
		for (unsigned int j = 0; j < p; ++j) {
			if (hasStoredSample(shift[k][ind2])) {
				correlation[k][j] += shift[k][ind1] * shift2[k][ind2];
				++ncorrelation[k][j];
			}
			--ind2;
			if (ind2 < 0) ind2 += p;
		}
	}
	else {
		int ind2 = ind1 - dmin;
		for (unsigned int j = dmin; j < p; ++j) {
			if (ind2 < 0) ind2 += p;
			if (hasStoredSample(shift[k][ind2])) {
				correlation[k][j] += shift[k][ind1] * shift2[k][ind2];
				++ncorrelation[k][j];
			}
			--ind2;
		}
	}

	++insertindex[k];
	if (insertindex[k] == p) insertindex[k] = 0;
}

void CrossCorrelator::clear() {
	Correlator::clear();

	for (unsigned int j = 0; j < numcorrelators; ++j)
		accumulator2[j] = 0.0;
}

void CrossCorrelator::save(FILE *fout) {
	Correlator::save(fout);
	for (unsigned int i = 0; i < p; ++i)
		for (unsigned int j = 0; j <= kmax; ++j)
			fprintf(fout, "%lg ", shift2[j][i]);
	for (unsigned int i = 0; i < kmax; ++i)
		fprintf(fout, "%lg ", accumulator2[i]);
}

void CrossCorrelator::read(FILE *fin) {
	Correlator::read(fin);

	shift2 = new double*[numcorrelators];
	accumulator2 = new double[numcorrelators];

	for (unsigned int j = 0; j < numcorrelators; ++j)
		shift2[j] = new double[p];

	for (unsigned int i = 0; i < p; ++i)
		for (unsigned int j = 0; j <= kmax; ++j)
			fscanf(fin, "%lg", &shift2[j][i]);
	for (unsigned int i = 0; i < kmax; ++i)
		fscanf(fin, "%lg", &accumulator2[i]);
}

/////////////////////////////////////////
// VectorCorrelator class
/////////////////////////////////////////
VectorCorrelator::VectorCorrelator(const unsigned int numcorrin, const unsigned int pin, const unsigned int min) {
	setsize(numcorrin, pin, min);
}


void VectorCorrelator::setsize(const unsigned int numcorrin, const unsigned int pin, const unsigned int min) {

	Correlator::setsize(numcorrin, pin, min);
	shift2 = new double*[numcorrelators];
	shift3 = new double*[numcorrelators];
	accumulator2 = new double[numcorrelators];
	accumulator3 = new double[numcorrelators];

	for (unsigned int j = 0; j < numcorrelators; ++j) {
		shift2[j] = new double[p];
		shift3[j] = new double[p];
	}
}

VectorCorrelator::~VectorCorrelator() {
	if (numcorrelators == 0) return;
	delete[] shift2;
	delete[] shift3;
	delete[] accumulator2;
	delete[] accumulator3;
}

void VectorCorrelator::initialize() {
	Correlator::initialize();

	for (unsigned int j = 0; j < numcorrelators; ++j) {
		accumulator2[j] = 0.0;
		accumulator3[j] = 0.0;
	}
}

void VectorCorrelator::add(const double w0, const double w1, const double w2, const unsigned int k) {
	/// Samples that would fall beyond the last multi-tau level are dropped.
	if (k == numcorrelators) return;
	if (k > kmax) kmax = k;

	/// Insert the vector sample at the current ring-buffer cursor.
	shift[k][insertindex[k]] = w0;
	shift2[k][insertindex[k]] = w1;
	shift3[k][insertindex[k]] = w2;

	/// Every m samples we forward the block average to the next coarser level.
	accumulator[k] += w0;
	accumulator2[k] += w1;
	accumulator3[k] += w2;
	++naccumulator[k];
	if (naccumulator[k] == m) {
		add(accumulator[k] / m, accumulator2[k] / m, accumulator3[k] / m, k + 1);
		accumulator[k] = 0;
		accumulator2[k] = 0;
		accumulator3[k] = 0;
		naccumulator[k] = 0;
	}

	/// The finest level stores every lag. Coarser levels start at dmin so the
	/// short-time window is not duplicated across levels.
	unsigned int ind1 = insertindex[k];
	if (k == 0) {
		int ind2 = ind1;
		for (unsigned int j = 0; j < p; ++j) {
			if (hasStoredSample(shift[k][ind2])) {
				correlation[k][j] += (shift[k][ind1] * shift[k][ind2] +
					shift2[k][ind1] * shift2[k][ind2] +
					shift3[k][ind1] * shift3[k][ind2]);
				++ncorrelation[k][j];
			}
			--ind2;
			if (ind2 < 0) ind2 += p;
		}
	}
	else {
		int ind2 = ind1 - dmin;
		for (unsigned int j = dmin; j < p; ++j) {
			if (ind2 < 0) ind2 += p;
			if (hasStoredSample(shift[k][ind2])) {
				correlation[k][j] += (shift[k][ind1] * shift[k][ind2] +
					shift2[k][ind1] * shift2[k][ind2] +
					shift3[k][ind1] * shift3[k][ind2]);
				++ncorrelation[k][j];
			}
			--ind2;
		}
	}

	++insertindex[k];
	if (insertindex[k] == p) insertindex[k] = 0;
}

void VectorCorrelator::clear() {
	Correlator::clear();

	for (unsigned int j = 0; j < numcorrelators; ++j) {
		accumulator2[j] = 0.0;
		accumulator3[j] = 0.0;
	}
}

void VectorCorrelator::save(FILE *fout) {
	Correlator::save(fout);
	for (unsigned int i = 0; i < p; ++i)
		for (unsigned int j = 0; j <= kmax; ++j)
			fprintf(fout, "%lg %lg ", shift2[j][i], shift3[j][i]);
	for (unsigned int i = 0; i < kmax; ++i)
		fprintf(fout, "%lg %lg ", accumulator2[i], accumulator3[i]);
}

void VectorCorrelator::read(FILE *fin) {
	Correlator::read(fin);

	shift2 = new double*[numcorrelators];
	shift3 = new double*[numcorrelators];
	accumulator2 = new double[numcorrelators];
	accumulator3 = new double[numcorrelators];

	for (unsigned int j = 0; j < numcorrelators; ++j) {
		shift2[j] = new double[p];
		shift3[j] = new double[p];
	}

	for (unsigned int i = 0; i < p; ++i)
		for (unsigned int j = 0; j <= kmax; ++j)
			fscanf(fin, "%lg %lg", &shift2[j][i], &shift3[j][i]);
	for (unsigned int i = 0; i < kmax; ++i)
		fscanf(fin, "%lg %lg", &accumulator2[i], &accumulator3[i]);
}

/////////////////////////////////////////
// Correlator6 class
/////////////////////////////////////////
Correlator6::Correlator6(const unsigned int numcorrin, const unsigned int pin, const unsigned int min) {
	setsize(numcorrin, pin, min);
}

void Correlator6::setsize(const unsigned int numcorrin, const unsigned int pin, const unsigned int min) {
	Correlator::setsize(numcorrin, pin, min);

	shift2 = new double*[numcorrelators];
	shift3 = new double*[numcorrelators];
	shift4 = new double*[numcorrelators];
	shift5 = new double*[numcorrelators];
	shift6 = new double*[numcorrelators];

	correlation2 = new double*[numcorrelators];
	correlation3 = new double*[numcorrelators];
	correlation4 = new double*[numcorrelators];
	correlation5 = new double*[numcorrelators];
	correlation6 = new double*[numcorrelators];

	accumulator2 = new double[numcorrelators];
	accumulator3 = new double[numcorrelators];
	accumulator4 = new double[numcorrelators];
	accumulator5 = new double[numcorrelators];
	accumulator6 = new double[numcorrelators];

	for (unsigned int j = 0; j < numcorrelators; ++j) {
		shift2[j] = new double[p];
		shift3[j] = new double[p];
		shift4[j] = new double[p];
		shift5[j] = new double[p];
		shift6[j] = new double[p];

		correlation2[j] = new double[p];
		correlation3[j] = new double[p];
		correlation4[j] = new double[p];
		correlation5[j] = new double[p];
		correlation6[j] = new double[p];
	}

	f2 = new double[length];
	f3 = new double[length];
	f4 = new double[length];
	f5 = new double[length];
	f6 = new double[length];
}

Correlator6::~Correlator6() {
	if (numcorrelators == 0) return;
	delete[] shift2;
	delete[] shift3;
	delete[] shift4;
	delete[] shift5;
	delete[] shift6;
	delete[] correlation2;
	delete[] correlation3;
	delete[] correlation4;
	delete[] correlation5;
	delete[] correlation6;
	delete[] accumulator2;
	delete[] accumulator3;
	delete[] accumulator4;
	delete[] accumulator5;
	delete[] accumulator6;
	delete[] f2;
	delete[] f3;
	delete[] f4;
	delete[] f5;
	delete[] f6;
}

void Correlator6::initialize() {
	Correlator::initialize();

	for (unsigned int j = 0; j < numcorrelators; ++j) {
		for (unsigned int i = 0; i < p; ++i) {
			shift2[j][i] = kUnusedCorrelatorSample;
			shift3[j][i] = kUnusedCorrelatorSample;
			shift4[j][i] = kUnusedCorrelatorSample;
			shift5[j][i] = kUnusedCorrelatorSample;
			shift6[j][i] = kUnusedCorrelatorSample;
			correlation2[j][i] = 0;
			correlation3[j][i] = 0;
			correlation4[j][i] = 0;
			correlation5[j][i] = 0;
			correlation6[j][i] = 0;
		}
		accumulator2[j] = 0.0;
		accumulator3[j] = 0.0;
		accumulator4[j] = 0.0;
		accumulator5[j] = 0.0;
		accumulator6[j] = 0.0;
	}

	for (unsigned int i = 0; i < length; ++i) {
		f2[i] = 0;
		f3[i] = 0;
		f4[i] = 0;
		f5[i] = 0;
		f6[i] = 0;
	}
}

void Correlator6::add(const double w1, const double w2, const double w3,
                      const double w4, const double w5, const double w6,
                      const unsigned int k) {
	if (k == numcorrelators) return;
	if (k > kmax) kmax = k;

	shift[k][insertindex[k]] = w1;
	shift2[k][insertindex[k]] = w2;
	shift3[k][insertindex[k]] = w3;
	shift4[k][insertindex[k]] = w4;
	shift5[k][insertindex[k]] = w5;
	shift6[k][insertindex[k]] = w6;

	accumulator[k] += w1;
	accumulator2[k] += w2;
	accumulator3[k] += w3;
	accumulator4[k] += w4;
	accumulator5[k] += w5;
	accumulator6[k] += w6;
	++naccumulator[k];
	if (naccumulator[k] == m) {
		add(accumulator[k] / m, accumulator2[k] / m, accumulator3[k] / m,
		    accumulator4[k] / m, accumulator5[k] / m, accumulator6[k] / m,
		    k + 1);
		accumulator[k] = 0;
		accumulator2[k] = 0;
		accumulator3[k] = 0;
		accumulator4[k] = 0;
		accumulator5[k] = 0;
		accumulator6[k] = 0;
		naccumulator[k] = 0;
	}

	unsigned int ind1 = insertindex[k];
	if (k == 0) {
		int ind2 = ind1;
		for (unsigned int j = 0; j < p; ++j) {
			if (hasStoredSample(shift[k][ind2])) {
				correlation[k][j] += shift[k][ind1] * shift[k][ind2];
				correlation2[k][j] += shift2[k][ind1] * shift2[k][ind2];
				correlation3[k][j] += shift3[k][ind1] * shift3[k][ind2];
				correlation4[k][j] += shift4[k][ind1] * shift4[k][ind2];
				correlation5[k][j] += shift5[k][ind1] * shift5[k][ind2];
				correlation6[k][j] += shift6[k][ind1] * shift6[k][ind2];
				++ncorrelation[k][j];
			}
			--ind2;
			if (ind2 < 0) ind2 += p;
		}
	}
	else {
		int ind2 = ind1 - dmin;
		for (unsigned int j = dmin; j < p; ++j) {
			if (ind2 < 0) ind2 += p;
			if (hasStoredSample(shift[k][ind2])) {
				correlation[k][j] += shift[k][ind1] * shift[k][ind2];
				correlation2[k][j] += shift2[k][ind1] * shift2[k][ind2];
				correlation3[k][j] += shift3[k][ind1] * shift3[k][ind2];
				correlation4[k][j] += shift4[k][ind1] * shift4[k][ind2];
				correlation5[k][j] += shift5[k][ind1] * shift5[k][ind2];
				correlation6[k][j] += shift6[k][ind1] * shift6[k][ind2];
				++ncorrelation[k][j];
			}
			--ind2;
		}
	}

	++insertindex[k];
	if (insertindex[k] == p) insertindex[k] = 0;
}

void Correlator6::evaluate() {
	unsigned int im = 0;

	for (unsigned int i = 0; i < p; ++i) {
		if (ncorrelation[0][i] > 0) {
			t[im] = i;
			f[im] = correlation[0][i] / ncorrelation[0][i];
			f2[im] = correlation2[0][i] / ncorrelation[0][i];
			f3[im] = correlation3[0][i] / ncorrelation[0][i];
			f4[im] = correlation4[0][i] / ncorrelation[0][i];
			f5[im] = correlation5[0][i] / ncorrelation[0][i];
			f6[im] = correlation6[0][i] / ncorrelation[0][i];
			++im;
		}
	}

	for (unsigned int k = 1; k < kmax; ++k) {
		for (unsigned int i = dmin; i < p; ++i) {
			if (ncorrelation[k][i] > 0) {
				t[im] = i * pow((double)m, k);
				f[im] = correlation[k][i] / ncorrelation[k][i];
				f2[im] = correlation2[k][i] / ncorrelation[k][i];
				f3[im] = correlation3[k][i] / ncorrelation[k][i];
				f4[im] = correlation4[k][i] / ncorrelation[k][i];
				f5[im] = correlation5[k][i] / ncorrelation[k][i];
				f6[im] = correlation6[k][i] / ncorrelation[k][i];
				++im;
			}
		}
	}

	npcorr = im;
}

void Correlator6::clear() {
	Correlator::clear();

	for (unsigned int j = 0; j < numcorrelators; ++j) {
		for (unsigned int i = 0; i < p; ++i) {
			shift2[j][i] = kUnusedCorrelatorSample;
			shift3[j][i] = kUnusedCorrelatorSample;
			shift4[j][i] = kUnusedCorrelatorSample;
			shift5[j][i] = kUnusedCorrelatorSample;
			shift6[j][i] = kUnusedCorrelatorSample;
			correlation2[j][i] = 0;
			correlation3[j][i] = 0;
			correlation4[j][i] = 0;
			correlation5[j][i] = 0;
			correlation6[j][i] = 0;
		}
		accumulator2[j] = 0.0;
		accumulator3[j] = 0.0;
		accumulator4[j] = 0.0;
		accumulator5[j] = 0.0;
		accumulator6[j] = 0.0;
	}

	for (unsigned int i = 0; i < length; ++i) {
		f2[i] = 0;
		f3[i] = 0;
		f4[i] = 0;
		f5[i] = 0;
		f6[i] = 0;
	}
}

/////////////////////////////////////////
// CrossVectorCorrelator class
/////////////////////////////////////////
CrossVectorCorrelator::CrossVectorCorrelator(const unsigned int numcorrin, const unsigned int pin, const unsigned int min) {
	setsize(numcorrin, pin, min);
	//   printf("CrossVectorCorrelator and derived classes: NOT TESTED!!!\n");
}


void CrossVectorCorrelator::setsize(const unsigned int numcorrin, const unsigned int pin, const unsigned int min) {

	Correlator::setsize(numcorrin, pin, min);
	shift2 = new double*[numcorrelators];
	shift3 = new double*[numcorrelators];
	shift4 = new double*[numcorrelators];
	shift5 = new double*[numcorrelators];
	shift6 = new double*[numcorrelators];
	accumulator2 = new double[numcorrelators];
	accumulator3 = new double[numcorrelators];
	accumulator4 = new double[numcorrelators];
	accumulator5 = new double[numcorrelators];
	accumulator6 = new double[numcorrelators];

	for (unsigned int j = 0; j < numcorrelators; ++j) {
		shift2[j] = new double[p];
		shift3[j] = new double[p];
		shift4[j] = new double[p];
		shift5[j] = new double[p];
		shift6[j] = new double[p];
	}
}

CrossVectorCorrelator::~CrossVectorCorrelator() {
	if (numcorrelators == 0) return;
	delete[] shift2;
	delete[] shift3;
	delete[] shift4;
	delete[] shift5;
	delete[] shift6;
	delete[] accumulator2;
	delete[] accumulator3;
	delete[] accumulator4;
	delete[] accumulator5;
	delete[] accumulator6;
}

void CrossVectorCorrelator::initialize() {
	Correlator::initialize();

	for (unsigned int j = 0; j < numcorrelators; ++j) {
		accumulator2[j] = 0.0;
		accumulator3[j] = 0.0;
		accumulator4[j] = 0.0;
		accumulator5[j] = 0.0;
		accumulator6[j] = 0.0;
	}
}

void CrossVectorCorrelator::add(const double wA0, const double wA1, const double wA2,
	const double wB0, const double wB1, const double wB2, const unsigned int k) {
	/// If we exceed the correlator side, the value is discarded
	if (k == numcorrelators) return;
	if (k > kmax) kmax = k;

	/// Insert new value in shift array
	shift[k][insertindex[k]] = wA0;
	shift2[k][insertindex[k]] = wA1;
	shift3[k][insertindex[k]] = wA2;
	shift4[k][insertindex[k]] = wB0;
	shift5[k][insertindex[k]] = wB1;
	shift6[k][insertindex[k]] = wB2;

	/// Add to accumulator and, if needed, add to next correlator
	accumulator[k] += wA0;
	accumulator2[k] += wA1;
	accumulator3[k] += wA2;
	accumulator4[k] += wB0;
	accumulator5[k] += wB1;
	accumulator6[k] += wB2;
	++naccumulator[k];
	if (naccumulator[k] == m) {
		add(accumulator[k] / m, accumulator2[k] / m, accumulator3[k] / m,
			accumulator4[k] / m, accumulator5[k] / m, accumulator6[k] / m, k + 1);
		accumulator[k] = 0;
		accumulator2[k] = 0;
		accumulator3[k] = 0;
		accumulator4[k] = 0;
		accumulator5[k] = 0;
		accumulator6[k] = 0;
		naccumulator[k] = 0;
	}

	/// Calculate correlation function
	unsigned int ind1 = insertindex[k];
	if (k == 0) { /// First correlator is different
		int ind2 = ind1;
		for (unsigned int j = 0; j < p; ++j) {
			if (shift[k][ind2] > -1e10) {
				correlation[k][j] += (shift[k][ind1] * shift4[k][ind2] +
					shift2[k][ind1] * shift5[k][ind2] +
					shift3[k][ind1] * shift6[k][ind2]);
				++ncorrelation[k][j];
			}
			--ind2;
			if (ind2 < 0) ind2 += p;
		}
	}
	else {
		int ind2 = ind1 - dmin;
		for (unsigned int j = dmin; j < p; ++j) {
			if (ind2 < 0) ind2 += p;
			if (shift[k][ind2] > -1e10) {
				correlation[k][j] += (shift[k][ind1] * shift4[k][ind2] +
					shift2[k][ind1] * shift5[k][ind2] +
					shift3[k][ind1] * shift6[k][ind2]);
				++ncorrelation[k][j];
			}
			--ind2;
		}
	}

	++insertindex[k];
	if (insertindex[k] == p) insertindex[k] = 0;
}

void CrossVectorCorrelator::clear() {
	Correlator::clear();

	for (unsigned int j = 0; j < numcorrelators; ++j) {
		accumulator2[j] = 0.0;
		accumulator3[j] = 0.0;
		accumulator4[j] = 0.0;
		accumulator5[j] = 0.0;
		accumulator6[j] = 0.0;
	}
}

void CrossVectorCorrelator::save(FILE *fout) {
	Correlator::save(fout);
	for (unsigned int i = 0; i < p; ++i)
		for (unsigned int j = 0; j <= kmax; ++j)
			fprintf(fout, "%lg %lg %lg %lg %lg ", shift2[j][i], shift3[j][i], shift4[j][i], shift5[j][i], shift6[j][i]);
	for (unsigned int i = 0; i < kmax; ++i)
		fprintf(fout, "%lg %lg %lg %lg %lg ", accumulator2[i], accumulator3[i], accumulator4[i], accumulator5[i], accumulator6[i]);
}

void CrossVectorCorrelator::read(FILE *fin) {
	Correlator::read(fin);

	shift2 = new double*[numcorrelators];
	shift3 = new double*[numcorrelators];
	shift4 = new double*[numcorrelators];
	shift5 = new double*[numcorrelators];
	shift6 = new double*[numcorrelators];
	accumulator2 = new double[numcorrelators];
	accumulator3 = new double[numcorrelators];
	accumulator4 = new double[numcorrelators];
	accumulator5 = new double[numcorrelators];
	accumulator6 = new double[numcorrelators];

	for (unsigned int j = 0; j < numcorrelators; ++j) {
		shift2[j] = new double[p];
		shift3[j] = new double[p];
		shift4[j] = new double[p];
		shift5[j] = new double[p];
		shift6[j] = new double[p];
	}

	for (unsigned int i = 0; i < p; ++i)
		for (unsigned int j = 0; j <= kmax; ++j)
			fscanf(fin, "%lg %lg %lg %lg %lg", &shift2[j][i], &shift3[j][i], &shift4[j][i], &shift5[j][i], &shift6[j][i]);
	for (unsigned int i = 0; i < kmax; ++i)
		fscanf(fin, "%lg %lg %lg %lg %lg", &accumulator2[i], &accumulator3[i], &accumulator4[i], &accumulator5[i], &accumulator6[i]);
}

/////////////////////////////////////////
// DiffusionCorrelator class
/////////////////////////////////////////
DiffusionCorrelator::DiffusionCorrelator(const unsigned int numcorrin, const unsigned int pin, const unsigned int min) :
	VectorCorrelator(numcorrin, pin, min) {}

void DiffusionCorrelator::add(const double w0, const double w1, const double w2, const unsigned int k) {
	/// If we exceed the correlator side, the value is discarded
	if (k == numcorrelators) return;
	if (k > kmax) kmax = k;

	/// Insert new value in shift array
	shift[k][insertindex[k]] = w0;
	shift2[k][insertindex[k]] = w1;
	shift3[k][insertindex[k]] = w2;

	/// Add to accumulator and, if needed, add to next correlator
	// Instead of adding the average, we add the last value of the position
	//accumulator[k] += w0;
	//accumulator2[k] += w1;
	//accumulator3[k] += w2;
	++naccumulator[k];
	if (naccumulator[k] == m) {
		//add(accumulator[k]/m, accumulator2[k]/m, accumulator3[k]/m, k+1);
		add(w0, w1, w2, k + 1);
		//accumulator[k]=0;
		//accumulator2[k]=0;
		//accumulator3[k]=0;
		naccumulator[k] = 0;
	}

	/// Calculate correlation function
	unsigned int ind1 = insertindex[k];
	if (k == 0) { /// First correlator is different
		int ind2 = ind1;
		for (unsigned int j = 0; j < p; ++j) {
			if (shift[k][ind2] > -1e10) {
				correlation[k][j] += (shift[k][ind1] - shift[k][ind2])*(shift[k][ind1] - shift[k][ind2]) +
					(shift2[k][ind1] - shift2[k][ind2])*(shift2[k][ind1] - shift2[k][ind2]) +
					(shift3[k][ind1] - shift3[k][ind2])*(shift3[k][ind1] - shift3[k][ind2]);
				++ncorrelation[k][j];
			}
			--ind2;
			if (ind2 < 0) ind2 += p;
		}
	}
	else {
		int ind2 = ind1 - dmin;
		for (unsigned int j = dmin; j < p; ++j) {
			if (ind2 < 0) ind2 += p;
			if (shift[k][ind2] > -1e10) {
				correlation[k][j] += (shift[k][ind1] - shift[k][ind2])*(shift[k][ind1] - shift[k][ind2]) +
					(shift2[k][ind1] - shift2[k][ind2])*(shift2[k][ind1] - shift2[k][ind2]) +
					(shift3[k][ind1] - shift3[k][ind2])*(shift3[k][ind1] - shift3[k][ind2]);
				++ncorrelation[k][j];
			}
			--ind2;
		}
	}

	++insertindex[k];
	if (insertindex[k] == p) insertindex[k] = 0;
}

/////////////////////////////////////////
// R4Correlator class
/////////////////////////////////////////
R4Correlator::R4Correlator(const unsigned int numcorrin, const unsigned int pin, const unsigned int min) :
	VectorCorrelator(numcorrin, pin, min) {}

void R4Correlator::add(const double w0, const double w1, const double w2, const unsigned int k) {
	/// If we exceed the correlator side, the value is discarded
	if (k == numcorrelators) return;
	if (k > kmax) kmax = k;

	/// Insert new value in shift array
	shift[k][insertindex[k]] = w0;
	shift2[k][insertindex[k]] = w1;
	shift3[k][insertindex[k]] = w2;

	/// Add to accumulator and, if needed, add to next correlator
	// Instead of adding the average, we add the last value of the position
	//accumulator[k] += w0;
	//accumulator2[k] += w1;
	//accumulator3[k] += w2;
	++naccumulator[k];
	if (naccumulator[k] == m) {
		//add(accumulator[k]/m, accumulator2[k]/m, accumulator3[k]/m, k+1);
		add(w0, w1, w2, k + 1);
		//accumulator[k]=0;
		//accumulator2[k]=0;
		//accumulator3[k]=0;
		naccumulator[k] = 0;
	}

	/// Calculate correlation function
	unsigned int ind1 = insertindex[k];
	if (k == 0) { /// First correlator is different
		int ind2 = ind1;
		for (unsigned int j = 0; j < p; ++j) {
			if (shift[k][ind2] > -1e10) {
				correlation[k][j] += pow((shift[k][ind1] - shift[k][ind2])*(shift[k][ind1] - shift[k][ind2]) +
					(shift2[k][ind1] - shift2[k][ind2])*(shift2[k][ind1] - shift2[k][ind2]) +
					(shift3[k][ind1] - shift3[k][ind2])*(shift3[k][ind1] - shift3[k][ind2]), 2.0);
				++ncorrelation[k][j];
			}
			--ind2;
			if (ind2 < 0) ind2 += p;
		}
	}
	else {
		int ind2 = ind1 - dmin;
		for (unsigned int j = dmin; j < p; ++j) {
			if (ind2 < 0) ind2 += p;
			if (shift[k][ind2] > -1e10) {
				correlation[k][j] += pow((shift[k][ind1] - shift[k][ind2])*(shift[k][ind1] - shift[k][ind2]) +
					(shift2[k][ind1] - shift2[k][ind2])*(shift2[k][ind1] - shift2[k][ind2]) +
					(shift3[k][ind1] - shift3[k][ind2])*(shift3[k][ind1] - shift3[k][ind2]), 2.0);
				++ncorrelation[k][j];
			}
			--ind2;
		}
	}

	++insertindex[k];
	if (insertindex[k] == p) insertindex[k] = 0;
}


/////////////////////////////////////////
// Anisotropic diffusion correlator
/////////////////////////////////////////
AnisotropicDiffusionCorrelator::AnisotropicDiffusionCorrelator(const unsigned int numcorrin, const unsigned int pin, const unsigned int min) {
	setsize(numcorrin, pin, min);
}

void AnisotropicDiffusionCorrelator::setsize(const unsigned int numcorrin, const unsigned int pin, const unsigned int min) {
	VectorCorrelator::setsize(numcorrin, pin, min);
	correlation2 = new double*[numcorrelators];
	shift4 = new double*[numcorrelators];
	shift5 = new double*[numcorrelators];
	shift6 = new double*[numcorrelators];

	for (unsigned int j = 0; j < numcorrelators; ++j) {
		shift4[j] = new double[p];
		shift5[j] = new double[p];
		shift6[j] = new double[p];
		correlation2[j] = new double[p];
	}

	f2 = new double[length];
}

AnisotropicDiffusionCorrelator::~AnisotropicDiffusionCorrelator() {
	if (numcorrelators == 0) return;
	delete[] shift4;
	delete[] shift5;
	delete[] shift6;
	delete[] correlation2;
	delete[] f2;
}

double AnisotropicDiffusionCorrelator::calcparcorr(const double r0x, const double r0y, const double r0z,
	const double u1x, const double u1y, const double u1z,
	const double r1x, const double r1y, const double r1z) {

	double uxx = u1x*u1x;
	double uxy = u1x*u1y;
	double uxz = u1x*u1z;
	double uyy = u1y*u1y;
	double uyz = u1y*u1z;
	double uzz = u1z*u1z;

	double rx = r1x - r0x;
	double ry = r1y - r0y;
	double rz = r1z - r0z;

	double vx = uxx*rx + uxy*ry + uxz*rz;
	double vy = uxy*rx + uyy*ry + uyz*rz;
	double vz = uxz*rx + uyz*ry + uzz*rz;

	return vx*vx + vy*vy + vz*vz;
}

// Perpendicular
double AnisotropicDiffusionCorrelator::calcpercorr(const double r0x, const double r0y, const double r0z,
	const double u1x, const double u1y, const double u1z,
	const double r1x, const double r1y, const double r1z) {

	double uxx = 1.0 - u1x*u1x;
	double uxy = -u1x*u1y;
	double uxz = -u1x*u1z;
	double uyy = 1.0 - u1y*u1y;
	double uyz = -u1y*u1z;
	double uzz = 1.0 - u1z*u1z;

	double rx = r1x - r0x;
	double ry = r1y - r0y;
	double rz = r1z - r0z;

	double vx = uxx*rx + uxy*ry + uxz*rz;
	double vy = uxy*rx + uyy*ry + uyz*rz;
	double vz = uxz*rx + uyz*ry + uzz*rz;

	return vx*vx + vy*vy + vz*vz;
}


void AnisotropicDiffusionCorrelator::add(const double w0, const double w1, const double w2, const double u0, const double u1, const double u2, const unsigned int k) {
	if (k == numcorrelators) return;
	if (k > kmax) kmax = k;

	shift[k][insertindex[k]] = w0;
	shift2[k][insertindex[k]] = w1;
	shift3[k][insertindex[k]] = w2;
	shift4[k][insertindex[k]] = u0;
	shift5[k][insertindex[k]] = u1;
	shift6[k][insertindex[k]] = u2;

	++naccumulator[k];
	if (naccumulator[k] == m) {
		add(w0, w1, w2, u0, u1, u2, k + 1);
		naccumulator[k] = 0;
	}

	unsigned int ind1 = insertindex[k];
	if (k == 0) {
		int ind2 = ind1;
		for (unsigned int j = 0; j < p; ++j) {
			if (shift[k][ind2] > -1e10) {
				correlation[k][j] += calcparcorr(shift[k][ind2], shift2[k][ind2], shift3[k][ind2],
					shift4[k][ind1], shift5[k][ind1], shift6[k][ind1],
					shift[k][ind1], shift2[k][ind1], shift3[k][ind1]);
				correlation2[k][j] += calcpercorr(shift[k][ind2], shift2[k][ind2], shift3[k][ind2],
					shift4[k][ind1], shift5[k][ind1], shift6[k][ind1],
					shift[k][ind1], shift2[k][ind1], shift3[k][ind1]);
				++ncorrelation[k][j];
			}
			--ind2;
			if (ind2 < 0) ind2 += p;
		}
	}
	else {
		int ind2 = ind1 - dmin;
		for (unsigned int j = dmin; j < p; ++j) {
			if (ind2 < 0) ind2 += p;
			if (shift[k][ind2] > -1e10) {
				correlation[k][j] += calcparcorr(shift[k][ind2], shift2[k][ind2], shift3[k][ind2],
					shift4[k][ind1], shift5[k][ind1], shift6[k][ind1],
					shift[k][ind1], shift2[k][ind1], shift3[k][ind1]);
				correlation2[k][j] += calcpercorr(shift[k][ind2], shift2[k][ind2], shift3[k][ind2],
					shift4[k][ind1], shift5[k][ind1], shift6[k][ind1],
					shift[k][ind1], shift2[k][ind1], shift3[k][ind1]);
				++ncorrelation[k][j];
			}
			--ind2;
		}
	}

	++insertindex[k];
	if (insertindex[k] == p) insertindex[k] = 0;
}


void AnisotropicDiffusionCorrelator::evaluate() {
	unsigned int im = 0;

	for (unsigned int i = 0; i < p; ++i) {
		if (ncorrelation[0][i] > 0) {
			t[im] = i;
			f[im] = correlation[0][i] / ncorrelation[0][i];
			f2[im] = correlation2[0][i] / ncorrelation[0][i];
			++im;
		}
	}

	for (unsigned int k = 1; k < kmax; ++k) {
		for (unsigned int i = dmin; i < p; ++i) {
			if (ncorrelation[k][i] > 0) {
				t[im] = i * pow((double)m, k);
				f[im] = correlation[k][i] / ncorrelation[k][i];
				f2[im] = correlation2[k][i] / ncorrelation[k][i];

				++im;
			}
		}
	}

	npcorr = im;
}

/////////////////////////////////////////
// SqtCorrelatorGaussianChain class
/////////////////////////////////////////
SqtCorrelatorGaussianChain::SqtCorrelatorGaussianChain(const unsigned int numcorrin, const unsigned int pin, const unsigned int min) :
	CrossVectorCorrelator(numcorrin, pin, min) {}

void SqtCorrelatorGaussianChain::add(const double c0, const double c1, const double c2,
	const double s0, const double s1, const double s2, const unsigned int k) {

	/// If we exceed the correlator side, the value is discarded
	if (k == numcorrelators) return;
	if (k > kmax) kmax = k;

	/// Insert new value in shift array
	shift[k][insertindex[k]] = c0;
	shift2[k][insertindex[k]] = c1;
	shift3[k][insertindex[k]] = c2;
	shift4[k][insertindex[k]] = s0;
	shift5[k][insertindex[k]] = s1;
	shift6[k][insertindex[k]] = s2;

	/// Add to accumulator and, if needed, add to next correlator
	accumulator[k] += c0;
	accumulator2[k] += c1;
	accumulator3[k] += c2;
	accumulator4[k] += s0;
	accumulator5[k] += s1;
	accumulator6[k] += s2;
	++naccumulator[k];
	if (naccumulator[k] == m) {
		add(accumulator[k] / m, accumulator2[k] / m, accumulator3[k] / m,
			accumulator4[k] / m, accumulator5[k] / m, accumulator6[k] / m, k + 1);
		accumulator[k] = 0;
		accumulator2[k] = 0;
		accumulator3[k] = 0;
		accumulator4[k] = 0;
		accumulator5[k] = 0;
		accumulator6[k] = 0;
		naccumulator[k] = 0;
	}

	/// Calculate correlation function
	unsigned int ind1 = insertindex[k];
	if (k == 0) { /// First correlator is different
		int ind2 = ind1;
		for (unsigned int j = 0; j < p; ++j) {
			if (shift[k][ind2] > -1e10) {
				correlation[k][j] += (shift[k][ind1] * shift[k][ind2] +
					shift2[k][ind1] * shift2[k][ind2] +
					shift3[k][ind1] * shift3[k][ind2] +
					shift4[k][ind1] * shift4[k][ind2] +
					shift5[k][ind1] * shift5[k][ind2] +
					shift6[k][ind1] * shift6[k][ind2]) / 3.0;
				++ncorrelation[k][j];
			}
			--ind2;
			if (ind2 < 0) ind2 += p;
		}
	}
	else {
		int ind2 = ind1 - dmin;
		for (unsigned int j = dmin; j < p; ++j) {
			if (ind2 < 0) ind2 += p;
			if (shift[k][ind2] > -1e10) {
				correlation[k][j] += (shift[k][ind1] * shift[k][ind2] +
					shift2[k][ind1] * shift2[k][ind2] +
					shift3[k][ind1] * shift3[k][ind2] +
					shift4[k][ind1] * shift4[k][ind2] +
					shift5[k][ind1] * shift5[k][ind2] +
					shift6[k][ind1] * shift6[k][ind2]) / 3.0;
				++ncorrelation[k][j];
			}
			--ind2;
		}
	}

	++insertindex[k];
	if (insertindex[k] == p) insertindex[k] = 0;
}

/////////////////////////////////////////
// SqtCorrelatorIsotropic class
/////////////////////////////////////////
SqtCorrelatorIsotropic::SqtCorrelatorIsotropic(const unsigned int numcorrin, const unsigned int pin, const unsigned int min) :
	VectorCorrelator(numcorrin, pin, min) {}

void SqtCorrelatorIsotropic::add(const double w0, const double w1, const double w2, const unsigned int k) {
	/// If we exceed the correlator side, the value is discarded
	if (k == numcorrelators) return;
	if (k > kmax) kmax = k;

	/// Insert new value in shift array
	shift[k][insertindex[k]] = w0;
	shift2[k][insertindex[k]] = w1;
	shift3[k][insertindex[k]] = w2;

	// Instead of adding the average, we add the last value of the position (as in diffusion)
	++naccumulator[k];
	if (naccumulator[k] == m) {
		add(w0, w1, w2, k + 1);
		naccumulator[k] = 0;
	}

	/// Calculate correlation function
	unsigned int ind1 = insertindex[k];
	if (k == 0) { /// First correlator is different
		int ind2 = ind1;
		for (unsigned int j = 0; j < p; ++j) {
			if (shift[k][ind2] > -1e10) {
				if (ind1 == ind2) {
					correlation[k][j] += 1.0;
				}
				else {
					double Rx = shift[k][ind1] - shift[k][ind2];
					double Ry = shift2[k][ind1] - shift2[k][ind2];
					double Rz = shift3[k][ind1] - shift3[k][ind2];
					double R = sqrt(Rx*Rx + Ry*Ry + Rz*Rz);
					double qRnow = q*R;
					correlation[k][j] += sin(qRnow) / qRnow;
				}
				++ncorrelation[k][j];
			}
			--ind2;
			if (ind2 < 0) ind2 += p;
		}
	}
	else {
		int ind2 = ind1 - dmin;
		for (unsigned int j = dmin; j < p; ++j) {
			if (ind2 < 0) ind2 += p;
			if (shift[k][ind2] > -1e10) {
				if (ind1 == ind2) {
					correlation[k][j] += 1.0;
				}
				else {
					double Rx = shift[k][ind1] - shift[k][ind2];
					double Ry = shift2[k][ind1] - shift2[k][ind2];
					double Rz = shift3[k][ind1] - shift3[k][ind2];
					double R = sqrt(Rx*Rx + Ry*Ry + Rz*Rz);
					double qRnow = q*R;
					correlation[k][j] += sin(qRnow) / qRnow;
				}
				++ncorrelation[k][j];
			}
			--ind2;
		}
	}

	++insertindex[k];
	if (insertindex[k] == p) insertindex[k] = 0;
}

/////////////////////////////////////////
// SqtCorrelatorIsotropicManyQ class
/////////////////////////////////////////
SqtCorrelatorIsotropicManyQ::SqtCorrelatorIsotropicManyQ(const unsigned int numcorrin, const unsigned int pin, const unsigned int min) :
	VectorCorrelator(numcorrin, pin, min) {}

SqtCorrelatorIsotropicManyQ::~SqtCorrelatorIsotropicManyQ() {
	delete[] f2;
	delete[] f2av;
	delete[] correlation2;
	delete[] q;
}

void SqtCorrelatorIsotropicManyQ::setQ(const int nqin, const double* qin) {
	nq = nqin;
	q = new double[nq];
	for (unsigned int i = 0; i<nq; i++) q[i] = qin[i];
	correlation2 = new double**[numcorrelators];
	for (unsigned int j = 0; j < numcorrelators; ++j) {
		correlation2[j] = new double*[p];
		for (unsigned int k = 0; k < p; ++k)
			correlation2[j][k] = new double[nq-1];
	}
	f2 = new double*[length];
	f2av = new double*[length];
	for (unsigned int k = 0; k < length; ++k) {
		f2[k] = new double[nq-1];
		f2av[k] = new double[nq-1];
	}

};

void SqtCorrelatorIsotropicManyQ::initialize() {
	VectorCorrelator::initialize();

	for (unsigned int j = 0; j < numcorrelators; ++j)
		for (unsigned int k = 0; k < p; ++k)
			for (unsigned int l = 0; l < nq - 1; ++l)
				correlation2[j][k][l] = 0;

	for (unsigned int i = 0; i < length; ++i) 
		for (unsigned int l = 0; l < nq - 1; ++l) {
			f2[i][l] = 0;
			f2av[i][l] = 0;
		}
}

void SqtCorrelatorIsotropicManyQ::add(const double w0, const double w1, const double w2, const unsigned int k) {
	/// If we exceed the correlator side, the value is discarded
	if (k == numcorrelators) return;
	if (k > kmax) kmax = k;

	/// Insert new value in shift array
	shift[k][insertindex[k]] = w0;
	shift2[k][insertindex[k]] = w1;
	shift3[k][insertindex[k]] = w2;

	// Instead of adding the average, we add the last value of the position (as in diffusion)
	++naccumulator[k];
	if (naccumulator[k] == m) {
		add(w0, w1, w2, k + 1);
		naccumulator[k] = 0;
	}

	/// Calculate correlation function
	unsigned int ind1 = insertindex[k];
	if (k == 0) { /// First correlator is different
		int ind2 = ind1;
		for (unsigned int j = 0; j < p; ++j) {
			if (shift[k][ind2] > -1e10) {
				if (ind1 == ind2) {
					correlation[k][j] += 1.0;
					for (unsigned int l = 1; l < nq; ++l)
						correlation2[k][j][l - 1] += 1.0;
				}
				else {
					double Rx = shift[k][ind1] - shift[k][ind2];
					double Ry = shift2[k][ind1] - shift2[k][ind2];
					double Rz = shift3[k][ind1] - shift3[k][ind2];
					double R = sqrt(Rx*Rx + Ry*Ry + Rz*Rz);
					for (unsigned int l = 0; l < nq; ++l) {
						double qRnow = q[l]*R;
						if (l==0)
							correlation[k][j] += sin(qRnow) / qRnow;
						else
							correlation2[k][j][l-1] += sin(qRnow) / qRnow;
					}
				}
				++ncorrelation[k][j];
			}
			--ind2;
			if (ind2 < 0) ind2 += p;
		}
	}
	else {
		int ind2 = ind1 - dmin;
		for (unsigned int j = dmin; j < p; ++j) {
			if (ind2 < 0) ind2 += p;
			if (shift[k][ind2] > -1e10) {
				if (ind1 == ind2) {
					correlation[k][j] += 1.0;
				}
				else {
					double Rx = shift[k][ind1] - shift[k][ind2];
					double Ry = shift2[k][ind1] - shift2[k][ind2];
					double Rz = shift3[k][ind1] - shift3[k][ind2];
					double R = sqrt(Rx*Rx + Ry*Ry + Rz*Rz);
					for (unsigned int l = 0; l < nq; ++l) {
						double qRnow = q[l]*R;
						if (l==0)
							correlation[k][j] += sin(qRnow) / qRnow;
						else
							correlation2[k][j][l-1] += sin(qRnow) / qRnow;
					}
				}
				++ncorrelation[k][j];
			}
			--ind2;
		}
	}

	++insertindex[k];
	if (insertindex[k] == p) insertindex[k] = 0;
}

void SqtCorrelatorIsotropicManyQ::evaluate() {
	unsigned int im = 0;

	// First correlator
	for (unsigned int i = 0; i < p; ++i) {
		if (ncorrelation[0][i] > 0) {
			t[im] = i;
			f[im] = correlation[0][i] / ncorrelation[0][i];
			for (unsigned int l = 1; l < nq; ++l)
				f2[im][l - 1] = correlation2[0][i][l - 1] / ncorrelation[0][i];
			++im;
		}
	}

	// Subsequent correlators
	for (unsigned int k = 1; k < kmax; ++k) {
		for (unsigned int i = dmin; i < p; ++i) {
			if (ncorrelation[k][i] > 0) {
				t[im] = i * pow((double)m, k);
				f[im] = correlation[k][i] / ncorrelation[k][i];
				for (unsigned int l = 1; l < nq; ++l)
					f2[im][l - 1] = correlation2[k][i][l - 1] / ncorrelation[k][i];
				++im;
			}
		}
	}

	npcorr = im;
}

void SqtCorrelatorIsotropicManyQ::toaverage() {
	for (unsigned int i = 0; i < npcorr; ++i) {
		fav[i] += f[i];
		tav[i] = t[i];
		for (unsigned int l = 1; l < nq; ++l)
			f2av[i][l - 1] += f2[i][l - 1];
	}
	if (npcorr > npcorrmax)
		npcorrmax = npcorr;
	++nexp;
}


void SqtCorrelatorIsotropicManyQ::clear() {
	for (unsigned int j = 0; j < numcorrelators; ++j) {
		for (unsigned int i = 0; i < p; ++i) {
			shift[j][i] = -2E10;
			correlation[j][i] = 0;
			for (unsigned int l = 0; l < nq - 1; ++l)
				correlation2[j][i][l] = 0;
			ncorrelation[j][i] = 0;
		}
		accumulator[j] = 0.0;
		naccumulator[j] = 0;
		insertindex[j] = 0;
	}

	for (unsigned int i = 0; i < length; ++i) {
		t[i] = 0;
		f[i] = 0;
		for (unsigned int l = 0; l < nq - 1; ++l)
			f2[i][l] = 0;
	}
	npcorr = 0;
	kmax = 0;
}

/////////////////////////////////////////
// ChainCorrelator class
/////////////////////////////////////////
ChainCorrelator::ChainCorrelator(const unsigned int numcorrin, const unsigned int pin, const unsigned int min, const unsigned int nresultsin, const unsigned int nmonin, const unsigned int dimin) {
	setsize(numcorrin, pin, min, nresultsin, nmonin, dimin);
}

ChainCorrelator::~ChainCorrelator() {

	if (numcorrelators == 0) return;

	delete[] shift;
	delete[] correlation;
	delete[] ncorrelation;
	//delete[] accumulator;
	delete[] naccumulator;
	delete[] insertindex;
	delete[] params;

	delete[] t;
	delete[] f;
	delete[] tav;
	delete[] fav;
}


void ChainCorrelator::setsize(const unsigned int numcorrin, const unsigned int pin, const unsigned int min, const unsigned int nresultsin, const unsigned int nmonin, const unsigned int dimin) {
	numcorrelators = numcorrin;
	p = pin;
	m = min;
	dmin = p / m;
	nresults = nresultsin;
	nmon = nmonin;
	dim = dimin;
	arraysize = nmon*dim;

	/* It can be optimized to
	length = p + (numcorrelators-1)*(p-p/m)
	= p*(numcorrelators - (numcorrelators-1)/m)) */
	length = numcorrelators*p;

	shift = new double**[numcorrelators];
	correlation = new double**[numcorrelators];
	ncorrelation = new unsigned long int*[numcorrelators];
	//accumulator = new double*[numcorrelators];
	naccumulator = new unsigned int[numcorrelators];
	insertindex = new unsigned int[numcorrelators];

	params = new double[nresults];

	for (unsigned int j = 0; j < numcorrelators; ++j) {
		//accumulator[j] = new double[arraysize];
		shift[j] = new double*[p];
		for (unsigned int k = 0; k < p; ++k)
			shift[j][k] = new double[arraysize];

		/* It can be optimized: Apart from correlator 0, correlation and ncorrelation arrays only use p/2 values */
		correlation[j] = new double*[p];
		for (unsigned int k = 0; k < p; ++k)
			correlation[j][k] = new double[nresults];
		ncorrelation[j] = new unsigned long int[p];
	}

	t = new double[length];
	f = new double*[length];
	tav = new double[length];
	fav = new double*[length];
	for (unsigned int k = 0; k < length; ++k) {
		f[k] = new double[nresults];
		fav[k] = new double[nresults];
	}
}


void ChainCorrelator::setparameters(const double *paramsin) {
	for (unsigned int k = 0; k < nresults; ++k)
		params[k] = paramsin[k];
}


void ChainCorrelator::initialize() {

	for (unsigned int j = 0; j < numcorrelators; ++j) {
		for (unsigned int i = 0; i < p; ++i) {
			shift[j][i][0] = -2E10;
			for (unsigned k = 0; k < nresults; ++k)
				correlation[j][i][k] = 0;
			ncorrelation[j][i] = 0;
		}
		//accumulator[j][0] = 0.0;
		naccumulator[j] = 0;
		insertindex[j] = 0;
	}

	for (unsigned int i = 0; i < length; ++i) {
		t[i] = 0;
		tav[i] = 0;
		for (unsigned int k = 0; k < nresults; ++k) {
			f[i][k] = 0;
			fav[i][k] = 0;
		}
	}

	npcorr = 0;
	npcorrmax = 0;
	nexp = 0;
	kmax = 0;
}

void ChainCorrelator::add(const double *w, const unsigned int k) {

	/// If we exceed the correlator side, the value is discarded
	if (k == numcorrelators) return;
	if (k > kmax) kmax = k;

	// Check that we are getting the right data
	//for (unsigned int l = 0; l < arraysize; ++l)
		//printf("lolailo %g \n", w[l]);

	/// Insert new value in shift array
	for (unsigned int l = 0; l < arraysize; ++l)
		shift[k][insertindex[k]][l] = w[l];

	/// Add to accumulator and, if needed, add to next correlator
	//accumulator[k] += w;
	++naccumulator[k];
	if (naccumulator[k] == m) {
		//add(accumulator[k] / m, k + 1);
		add(w, k + 1);
		//accumulator[k] = 0;
		naccumulator[k] = 0;
	}

	/// Calculate correlation function
	unsigned int ind1 = insertindex[k];
	if (k == 0) { /// First correlator is different
		int ind2 = ind1;
		for (unsigned int j = 0; j < p; ++j) {
			if (shift[k][ind2][0] > -1e10) {
				for (unsigned int l = 0; l < nresults; ++l) {
					int monaux = (int)params[l];
					for (unsigned int ll = 0; ll < 3; ++ll) // MSD of monomer number given by params
						correlation[k][j][l] += pow(shift[k][ind1][3 * monaux + ll] - shift[k][ind2][3 * monaux + ll], 2.0);
				}
				++ncorrelation[k][j];
			}
			--ind2;
			if (ind2 < 0) ind2 += p;
		}
	}
	else {
		int ind2 = ind1 - dmin;
		for (unsigned int j = dmin; j < p; ++j) {
			if (ind2 < 0) ind2 += p;
			if (shift[k][ind2][0] > -1e10) {
				for (unsigned int l = 0; l < nresults; ++l) {
					int monaux = (int)params[l];
					for (unsigned int ll = 0; ll < 3; ++ll) // MSD of monomer number given by params
						correlation[k][j][l] += pow(shift[k][ind1][3 * monaux + ll] - shift[k][ind2][3 * monaux + ll], 2.0);
				}
				++ncorrelation[k][j];
			}
			--ind2;
		}
	}

	++insertindex[k];
	if (insertindex[k] == p) insertindex[k] = 0;
}

void ChainCorrelator::evaluate() {
	unsigned int im = 0;

	// First correlator
	for (unsigned int i = 0; i < p; ++i) {
		if (ncorrelation[0][i] > 0) {
			t[im] = i;
			for (unsigned int l = 0; l < nresults; ++l)
				f[im][l] = correlation[0][i][l] / ncorrelation[0][i];
			++im;
		}
	}

	// Subsequent correlators
	for (unsigned int k = 1; k < kmax; ++k) {
		for (unsigned int i = dmin; i < p; ++i) {
			if (ncorrelation[k][i] > 0) {
				t[im] = i * pow((double)m, k);
				for (unsigned int l = 0; l < nresults; ++l)
					f[im][l] = correlation[k][i][l] / ncorrelation[k][i];
				++im;
			}
		}
	}

	npcorr = im;
}

void ChainCorrelator::toaverage() {
	for (unsigned int i = 0; i < npcorr; ++i) {
		for (unsigned int l = 0; l < nresults; ++l)
			fav[i][l] += f[i][l];
		tav[i] = t[i];
	}
	if (npcorr > npcorrmax)
		npcorrmax = npcorr;
	++nexp;
}


void ChainCorrelator::clear() {
	for (unsigned int j = 0; j < numcorrelators; ++j) {
		for (unsigned int i = 0; i < p; ++i) {
			shift[j][i][0] = -2E10;
			for (unsigned int l = 0; l < nresults; ++l)
				correlation[j][i][l] = 0;
			ncorrelation[j][i] = 0;
		}
		//accumulator[j] = 0.0;
		naccumulator[j] = 0;
		insertindex[j] = 0;
	}

	for (unsigned int i = 0; i < length; ++i) {
		t[i] = 0;
		for (unsigned int l = 0; l < nresults; ++l)
			f[i][l] = 0;
	}
	npcorr = 0;
	kmax = 0;
}


SqtChainCorrelator::SqtChainCorrelator(const unsigned int numcorrin, const unsigned int pin, const unsigned int min, const unsigned int nresultsin, const unsigned int nmonin, const unsigned int dimin) :
	ChainCorrelator(numcorrin, pin, min, nresultsin, nmonin, dimin) {}


void SqtChainCorrelator::add(const double *w, const unsigned int k) {

	/// If we exceed the correlator side, the value is discarded
	if (k == numcorrelators) return;
	if (k > kmax) kmax = k;

	/// Insert new value in shift array
	for (unsigned int l = 0; l < arraysize; ++l)
		shift[k][insertindex[k]][l] = w[l];

	/// Add to accumulator and, if needed, add to next correlator
	//accumulator[k] += w;
	++naccumulator[k];
	if (naccumulator[k] == m) {
		//add(accumulator[k] / m, k + 1);
		add(w, k + 1);
		//accumulator[k] = 0;
		naccumulator[k] = 0;
	}

	/// Calculate correlation function
	unsigned int ind1 = insertindex[k];
	if (k == 0) { /// First correlator is different // BE CAREFUL WITH j=0 IN FIRST CORRELATOR!!! lim_{x\to 0} (sin(x)/x) = 1
		for (unsigned int i = 0; i < nmon; ++i) {
			for (unsigned int l = 0; l < nresults; ++l)
				correlation[k][0][l] += 1.0 / nmon;
			for (unsigned int q = i + 1; q < nmon; ++q) {
				double Rx = shift[k][ind1][3 * i] - shift[k][ind1][3 * q];
				double Ry = shift[k][ind1][3 * i + 1] - shift[k][ind1][3 * q + 1];
				double Rz = shift[k][ind1][3 * i + 2] - shift[k][ind1][3 * q + 2];
				double R = sqrt(Rx*Rx + Ry*Ry + Rz*Rz);
				for (unsigned int l = 0; l < nresults; ++l) {
					double qRnow = params[l] * R;
					correlation[k][0][l] += 2.0 * sin(qRnow) / qRnow / nmon;
				}
			}
		}
		++ncorrelation[k][0];

		int ind2 = ind1-1;
		if (ind2 < 0) ind2 += p;
		for (unsigned int j = 1; j < p; ++j) { 
			if (shift[k][ind2][0] > -1e10) {
				for (unsigned int i = 0; i < nmon; ++i) {
					for (unsigned int q = 0; q < nmon; ++q) {
						double Rx = shift[k][ind1][3 * i] - shift[k][ind2][3 * q];
						double Ry = shift[k][ind1][3 * i + 1] - shift[k][ind2][3 * q + 1];
						double Rz = shift[k][ind1][3 * i + 2] - shift[k][ind2][3 * q + 2];
						double R = sqrt(Rx*Rx + Ry*Ry + Rz*Rz);
						for (unsigned int l = 0; l < nresults; ++l) {
							double qRnow = params[l]*R;
							correlation[k][j][l] += sin(qRnow) / qRnow / nmon;
						}
					}
				}
				++ncorrelation[k][j];
			}
			--ind2;
			if (ind2 < 0) ind2 += p;
		}
	}
	else {
		int ind2 = ind1 - dmin;
		for (unsigned int j = dmin; j < p; ++j) {
			if (ind2 < 0) ind2 += p;
			if (shift[k][ind2][0] > -1e10) {
				for (unsigned int i = 0; i < nmon; ++i) {
					for (unsigned int q = 0; q < nmon; ++q) {
						double Rx = shift[k][ind1][3 * i] - shift[k][ind2][3 * q];
						double Ry = shift[k][ind1][3 * i + 1] - shift[k][ind2][3 * q + 1];
						double Rz = shift[k][ind1][3 * i + 2] - shift[k][ind2][3 * q + 2];
						double R = sqrt(Rx*Rx + Ry*Ry + Rz*Rz);
						for (unsigned int l = 0; l < nresults; ++l) {
							double qRnow = params[l] * R;
							correlation[k][j][l] += sin(qRnow) / qRnow / nmon;
						}
					}
				}
				++ncorrelation[k][j];
			}
			--ind2;
		}
	}

	++insertindex[k];
	if (insertindex[k] == p) insertindex[k] = 0;
}


PDFDisplacementCorrelator::PDFDisplacementCorrelator(const unsigned int numcorrin, const unsigned int pin, const unsigned int min, const unsigned int nresultsin, const unsigned int nmonin, const unsigned int dimin) :
	ChainCorrelator(numcorrin, pin, min, nresultsin, nmonin, dimin) {
	dmax = new double[length];
}

void PDFDisplacementCorrelator::setsize(const unsigned int numcorrin, const unsigned int pin, const unsigned int min, const unsigned int nresultsin, const unsigned int nmonin, const unsigned int dimin) {
	ChainCorrelator::setsize(numcorrin, pin, min, nresultsin, nmonin, dimin);
	dmax = new double[length];
}

void PDFDisplacementCorrelator::add(const double *w, const unsigned int k) {

	/// If we exceed the correlator side, the value is discarded
	if (k == numcorrelators) return;
	if (k > kmax) kmax = k;

	// Check that we are getting the right data
	//for (unsigned int l = 0; l < arraysize; ++l)
		//printf("lolailo %g \n", w[l]);

	/// Insert new value in shift array
	for (unsigned int l = 0; l < arraysize; ++l)
		shift[k][insertindex[k]][l] = w[l];

	/// Add to accumulator and, if needed, add to next correlator
	//accumulator[k] += w;
	++naccumulator[k];
	if (naccumulator[k] == m) {
		//add(accumulator[k] / m, k + 1);
		add(w, k + 1);
		//accumulator[k] = 0;
		naccumulator[k] = 0;
	}

	/// Calculate correlation function
	unsigned int ind1 = insertindex[k];
	if (k == 0) { /// First correlator is different
		int ind2 = ind1;
		for (unsigned int j = 0; j < p; ++j) {
			if (shift[k][ind2][0] > -1e10) {
				for (unsigned int l = 0; l < nmon; ++l) {
					double disp = shift[k][ind1][3 * l] - shift[k][ind2][3 * l]; // Only X component
					int bin = floor((disp + params[k]) / 2.0 / params[k] * nresults);
					if (bin < nresults)
						correlation[k][j][bin] += 1;
				}
				++ncorrelation[k][j];
			}
			--ind2;
			if (ind2 < 0) ind2 += p;
		}
	}
	else {
		int ind2 = ind1 - dmin;
		for (unsigned int j = dmin; j < p; ++j) {
			if (ind2 < 0) ind2 += p;
			if (shift[k][ind2][0] > -1e10) {
				for (unsigned int l = 0; l < nmon; ++l) {
					double disp = shift[k][ind1][3 * l] - shift[k][ind2][3 * l]; // Only X component
					int bin = floor((disp + params[k]) / 2.0 / params[k] * nresults);
					if (bin < nresults)
						correlation[k][j][bin] += 1;
				}
				++ncorrelation[k][j];
			}
			--ind2;
		}
	}

	++insertindex[k];
	if (insertindex[k] == p) insertindex[k] = 0;
}

void PDFDisplacementCorrelator::evaluate() {
	unsigned int im = 0;

	// First correlator
	for (unsigned int i = 0; i < p; ++i) {
		if (ncorrelation[0][i] > 0) {
			t[im] = i;
			dmax[im] = params[0];
			for (unsigned int l = 0; l < nresults; ++l)
				f[im][l] = correlation[0][i][l] / ncorrelation[0][i] / nmon / 2.0 / params[0] * nresults / (im + 1);
			++im;
		}
	}

	// Subsequent correlators
	for (unsigned int k = 1; k < kmax; ++k) {
		for (unsigned int i = dmin; i < p; ++i) {
			if (ncorrelation[k][i] > 0) {
				t[im] = i * pow((double)m, k);
				dmax[im] = params[k];
				for (unsigned int l = 0; l < nresults; ++l)
					f[im][l] = correlation[k][i][l] / ncorrelation[k][i] / nmon / 2.0 / params[0] * nresults / (im + 1);
				++im;
			}
		}
	}

	npcorr = im;
}


NGPDisplacementCorrelator::NGPDisplacementCorrelator(const unsigned int numcorrin, const unsigned int pin, const unsigned int min, const unsigned int nresultsin, const unsigned int nmonin, const unsigned int dimin) :
	ChainCorrelator(numcorrin, pin, min, nresultsin, nmonin, dimin) {}

void NGPDisplacementCorrelator::setsize(const unsigned int numcorrin, const unsigned int pin, const unsigned int min, const unsigned int nresultsin, const unsigned int nmonin, const unsigned int dimin) {
	ChainCorrelator::setsize(numcorrin, pin, min, nresultsin, nmonin, dimin);
}

void NGPDisplacementCorrelator::add(const double *w, const unsigned int k) {

	/// If we exceed the correlator side, the value is discarded
	if (k == numcorrelators) return;
	if (k > kmax) kmax = k;

	// Check that we are getting the right data
	//for (unsigned int l = 0; l < arraysize; ++l)
		//printf("lolailo %g \n", w[l]);

	/// Insert new value in shift array
	for (unsigned int l = 0; l < arraysize; ++l)
		shift[k][insertindex[k]][l] = w[l];

	/// Add to accumulator and, if needed, add to next correlator
	//accumulator[k] += w;
	++naccumulator[k];
	if (naccumulator[k] == m) {
		//add(accumulator[k] / m, k + 1);
		add(w, k + 1);
		//accumulator[k] = 0;
		naccumulator[k] = 0;
	}

	/// Calculate correlation function
	unsigned int ind1 = insertindex[k];
	if (k == 0) { /// First correlator is different
		int ind2 = ind1;
		for (unsigned int j = 0; j < p; ++j) {
			if (shift[k][ind2][0] > -1e10) {
				for (unsigned int l = 0; l < nmon; ++l) {
					if (dim==1) {
						double dx = shift[k][ind1][3 * l] - shift[k][ind2][3 * l];
						double r2 = dx*dx;
						double r4 = r2*r2;
						correlation[k][j][0] += r2;
						correlation[k][j][1] += r4;
					}
					else if (dim==2) {
						double dx = shift[k][ind1][3 * l] - shift[k][ind2][3 * l];
						double dy = shift[k][ind1][3 * l+1] - shift[k][ind2][3 * l+1];
						double r2 = dx*dx + dy*dy;
						double r4 = r2*r2;
						correlation[k][j][0] += r2;
						correlation[k][j][1] += r4;
					}
					else if (dim==3) {
						double dx = shift[k][ind1][3 * l] - shift[k][ind2][3 * l];
						double dy = shift[k][ind1][3 * l+1] - shift[k][ind2][3 * l+1];
						double dz = shift[k][ind1][3 * l+2] - shift[k][ind2][3 * l+2];
						double r2 = dx*dx + dy*dy + dz*dz;
						double r4 = r2*r2;
						correlation[k][j][0] += r2;
						correlation[k][j][1] += r4;
					}
				}
				++ncorrelation[k][j];
			}
			--ind2;
			if (ind2 < 0) ind2 += p;
		}
	}
	else {
		int ind2 = ind1 - dmin;
		for (unsigned int j = dmin; j < p; ++j) {
			if (ind2 < 0) ind2 += p;
			if (shift[k][ind2][0] > -1e10) {
				for (unsigned int l = 0; l < nmon; ++l) {
					if (dim==1) {
						double dx = shift[k][ind1][3 * l] - shift[k][ind2][3 * l];
						double r2 = dx*dx;
						double r4 = r2*r2;
						correlation[k][j][0] += r2;
						correlation[k][j][1] += r4;
					}
					else if (dim==2) {
						double dx = shift[k][ind1][3 * l] - shift[k][ind2][3 * l];
						double dy = shift[k][ind1][3 * l+1] - shift[k][ind2][3 * l+1];
						double r2 = dx*dx + dy*dy;
						double r4 = r2*r2;
						correlation[k][j][0] += r2;
						correlation[k][j][1] += r4;
					}
					else if (dim==3) {
						double dx = shift[k][ind1][3 * l] - shift[k][ind2][3 * l];
						double dy = shift[k][ind1][3 * l+1] - shift[k][ind2][3 * l+1];
						double dz = shift[k][ind1][3 * l+2] - shift[k][ind2][3 * l+2];
						double r2 = dx*dx + dy*dy + dz*dz;
						double r4 = r2*r2;
						correlation[k][j][0] += r2;
						correlation[k][j][1] += r4;
					}
				}
				++ncorrelation[k][j];
			}
			--ind2;
		}
	}

	++insertindex[k];
	if (insertindex[k] == p) insertindex[k] = 0;
}

void NGPDisplacementCorrelator::evaluate() {
	unsigned int im = 0;

	// First correlator
	for (unsigned int i = 0; i < p; ++i) {
		if (ncorrelation[0][i] > 0) {
			t[im] = i;
			f[im][0] = correlation[0][i][0]/ncorrelation[0][i]/nmon;
			f[im][1] = correlation[0][i][1]/ncorrelation[0][i]/nmon;
			if (dim==1) 
				f[im][2] = f[im][1]/3.0/f[im][0]/f[im][0] - 1.0;
			else if (dim==2)
				f[im][2] = 2.0*f[im][1]/4.0/f[im][0]/f[im][0] - 1.0;
			else if (dim==3)
				f[im][2] = 3.0*f[im][1]/5.0/f[im][0]/f[im][0] - 1.0;
			++im;
		}
	}

	// Subsequent correlators
	for (unsigned int k = 1; k < kmax; ++k) {
		for (unsigned int i = dmin; i < p; ++i) {
			if (ncorrelation[k][i] > 0) {
				t[im] = i * pow((double)m, k);
				f[im][0] = correlation[k][i][0] / ncorrelation[k][i] / nmon;
				f[im][1] = correlation[k][i][1] / ncorrelation[k][i] / nmon;
				if (dim==1) 
					f[im][2] = f[im][1]/3.0/f[im][0]/f[im][0] - 1.0;
				else if (dim==2)
					f[im][2] = 2.0*f[im][1]/4.0/f[im][0]/f[im][0] - 1.0;
				else if (dim==3)
					f[im][2] = 3.0*f[im][1]/5.0/f[im][0]/f[im][0] - 1.0;
				++im;
			}
		}
	}

	npcorr = im;
}

Chi4Correlator::Chi4Correlator(const unsigned int numcorrin, const unsigned int pin, const unsigned int min, const unsigned int nresultsin, const unsigned int nmonin, const unsigned int dimin) :
	ChainCorrelator(numcorrin, pin, min, nresultsin, nmonin, dimin) {}

void Chi4Correlator::setsize(const unsigned int numcorrin, const unsigned int pin, const unsigned int min, const unsigned int nresultsin, const unsigned int nmonin, const unsigned int dimin) {
	ChainCorrelator::setsize(numcorrin, pin, min, nresultsin, nmonin, dimin);
}


void Chi4Correlator::add(const double *w, const unsigned int k) {

	/// If we exceed the correlator side, the value is discarded
	if (k == numcorrelators) return;
	if (k > kmax) kmax = k;

	/// Insert new value in shift array
	for (unsigned int l = 0; l < arraysize; ++l)
		shift[k][insertindex[k]][l] = w[l];

	/// Add to accumulator and, if needed, add to next correlator
	//accumulator[k] += w;
	++naccumulator[k];
	if (naccumulator[k] == m) {
		add(w, k + 1);
		naccumulator[k] = 0;
	}

	/// Calculate correlation function
	unsigned int ind1 = insertindex[k];
	if (k == 0) { /// First correlator is different
		int ind2 = ind1;
		for (unsigned int j = 0; j < p; ++j) {
			if (shift[k][ind2][0] > -1e10) {
				// Calculate Q(t)
				double Q=0;
				for (unsigned int l=0; l < nmon; ++l) {
					double mux = shift[k][ind1][3*l] - shift[k][ind2][3*l];
					double muy = shift[k][ind1][3*l+1] - shift[k][ind2][3*l+1];
					double muz = shift[k][ind1][3*l+2] - shift[k][ind2][3*l+2];
					mux -= Lx * nearbyint(mux * Lxinv);
					muy -= Ly * nearbyint(muy * Lyinv);
					muz -= Lz * nearbyint(muz * Lzinv);
					for (unsigned int m=0; m<nmon; ++m) {
						double rijx = shift[k][ind2][3*m] - shift[k][ind2][3*l];
						double rijy = shift[k][ind2][3*m+1] - shift[k][ind2][3*l+1];
						double rijz = shift[k][ind2][3*m+2] - shift[k][ind2][3*l+2];
						rijx -= Lx * nearbyint(rijx * Lxinv);
						rijy -= Ly * nearbyint(rijy * Lyinv);
						rijz -= Lz * nearbyint(rijz * Lzinv);
						double distsq = (rijx-mux)*(rijx-mux)+(rijy-muy)*(rijy-muy)+(rijz-muz)*(rijz-muz);
						if (distsq<asq)
							Q+=1;
					}
				}
				correlation[k][j][0] += Q*Q;
				correlation[k][j][1] += Q;
				++ncorrelation[k][j];
			}
			--ind2;
			if (ind2 < 0) ind2 += p;
		}
	}
	else {
		int ind2 = ind1 - dmin;
		for (unsigned int j = dmin; j < p; ++j) {
			if (ind2 < 0) ind2 += p;
			if (shift[k][ind2][0] > -1e10) {
				// Calculate Q(t)
				double Q=0;
				for (unsigned int l=0; l < nmon; ++l) {
					double mux = shift[k][ind1][3*l] - shift[k][ind2][3*l];
					double muy = shift[k][ind1][3*l+1] - shift[k][ind2][3*l+1];
					double muz = shift[k][ind1][3*l+2] - shift[k][ind2][3*l+2];
					mux -= Lx * nearbyint(mux * Lxinv);
					muy -= Ly * nearbyint(muy * Lyinv);
					muz -= Lz * nearbyint(muz * Lzinv);
					for (unsigned int m=0; m<nmon; ++m) {
						double rijx = shift[k][ind2][3*m] - shift[k][ind2][3*l];
						double rijy = shift[k][ind2][3*m+1] - shift[k][ind2][3*l+1];
						double rijz = shift[k][ind2][3*m+2] - shift[k][ind2][3*l+2];
						rijx -= Lx * nearbyint(rijx * Lxinv);
						rijy -= Ly * nearbyint(rijy * Lyinv);
						rijz -= Lz * nearbyint(rijz * Lzinv);
						double distsq = (rijx-mux)*(rijx-mux)+(rijy-muy)*(rijy-muy)+(rijz-muz)*(rijz-muz);
						if (distsq<asq)
							Q+=1;
					}
				}
				correlation[k][j][0] += Q*Q;
				correlation[k][j][1] += Q;
				++ncorrelation[k][j];
			}
			--ind2;
		}
	}

	++insertindex[k];
	if (insertindex[k] == p) insertindex[k] = 0;
}

void Chi4Correlator::evaluate() {
	unsigned int im = 0;

	// First correlator
	for (unsigned int i = 0; i < p; ++i) {
		if (ncorrelation[0][i] > 0) {
			t[im] = i;
			f[im][0] = (correlation[0][i][0] / ncorrelation[0][i]-(correlation[0][i][1] / ncorrelation[0][i])*(correlation[0][i][1] / ncorrelation[0][i]))/nmon/nmon;
			f[im][1] = 0;
			++im;
		}
	}

	// Subsequent correlators
	for (unsigned int k = 1; k < kmax; ++k) {
		for (unsigned int i = dmin; i < p; ++i) {
			if (ncorrelation[k][i] > 0) {
				t[im] = i * pow((double)m, k);
				f[im][0] = (correlation[k][i][0] / ncorrelation[k][i]-(correlation[k][i][1] / ncorrelation[k][i])*(correlation[k][i][1] / ncorrelation[k][i]))/nmon/nmon;
				f[im][1] = 0;	
				++im;
			}
		}
	}

	npcorr = im;
}
