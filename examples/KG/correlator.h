/// Definition of correlator classes
#ifndef __correlator_h
#define __correlator_h

#include <stdio.h>

////////////////////////////////////////////////////
/// Standard Scalar Correlator f(tau)=<A(t)A(t+tau)>
class Correlator {

protected:
	/** Where the coming values are stored */
	double **shift;
	/** Array containing the actual calculated correlation function */
	double **correlation;
	/** Number of values accumulated in cor */
	unsigned long int **ncorrelation;

	/** Accumulator in each correlator */
	double *accumulator;
	/** Index that controls accumulation in each correlator */
	unsigned int *naccumulator;
	/** Index pointing at the position at which the current value is inserted */
	unsigned int *insertindex;

	/** Number of Correlators */
	unsigned int numcorrelators;

	/** Points per correlator */
	unsigned int p;
	/** Number of points over which to average; RECOMMENDED: p mod m = 0 */
	unsigned int m; 
	/** Minimum distance between points for correlators k>0; dmin = p/m */
	unsigned int dmin;

	/*  SCHEMATIC VIEW OF EACH CORRELATOR
						        p=N
		<----------------------------------------------->
		_________________________________________________
		|0|1|2|3|.|.|.| | | | | | | | | | | | | | | |N-1|
		-------------------------------------------------
		*/

	/** Lenght of result arrays */
	unsigned int length;
	/** Maximum correlator attained during simulation */
	unsigned int kmax;

public:
	double *t, *f, *tav, *fav;
	unsigned int npcorr, npcorrmax, nexp;

	/** Constructor */
	Correlator () {numcorrelators=0;} ;
	Correlator (const unsigned int numcorrin, const unsigned int pin, const unsigned int min);
	~Correlator();

	/** Set size of correlator */
	void setsize (const unsigned int numcorrin = 32, const unsigned int pin = 16, const unsigned int min = 2);

	/** Add a scalar to the correlator number k */
	void add(const double w, const unsigned int k = 0);

	/** Evaluate the current state of the correlator */
	void evaluate();

	/** Initialize all values (current and average) to zero */
	void initialize();

	/** Send current experiment values to the average arrays */
	void toaverage();

	/** Clear current arrays to zero */
	void clear();

	/** Save contents of correlator to file */
	void save(FILE *f);

	/** Read contents of correlator from file */
	void read(FILE *f);

        // Return t and f
        double gett(int i) {return t[i];}
        double getf(int i) {return f[i];}

	};

        

/////////////////////////////////////////////////////////////////////////////
/// Class for cross Correlations between two quantities f(tau)=<A(t)B(t+tau)>
class CrossCorrelator : public Correlator {

protected:

	// We need duplicates of these arrays
	double **shift2;
	double *accumulator2;

public:

	CrossCorrelator () {numcorrelators=0;} ;
	CrossCorrelator (const unsigned int numcorrin, const unsigned int pin, const unsigned int min);
	~CrossCorrelator();

	void setsize (const unsigned int numcorrin = 32, const unsigned int pin = 16, const unsigned int min = 2);

	void add(const double wA, const double wB, const unsigned int k = 0);

	void initialize();
	void clear();

	void save(FILE *f);
	void read(FILE *f);
	};

//////////////////////////////////////////////////////////////////////////////////
/// Class for Vector Correlations f(tau)=<A(t).A(t+tau)> (A=vector, .=dot product)
class VectorCorrelator : public Correlator {

protected:

	// We need three copies of these arrays
	double **shift2;
	double **shift3;
	double *accumulator2;
	double *accumulator3;

public:

	VectorCorrelator () {numcorrelators=0;} ;
	VectorCorrelator (const unsigned int numcorrin, const unsigned int pin, const unsigned int min);
	~VectorCorrelator();

	void setsize (const unsigned int numcorrin = 32, const unsigned int pin = 16, const unsigned int min = 2);

	void add(const double w0, const double w1, const double w2, const unsigned int k = 0);

	void initialize();
	void clear();

	void save(FILE *f);
	void read(FILE *f);
	};

//////////////////////////////////////////////////////////////////////////////////////////////////////////////////
/// Class for cross Correlations between two vector quantities f(tau)=<A(t).B(t+tau)>  (A,B=vector, .=dot product)
class CrossVectorCorrelator : public Correlator {

protected:

	// We need three copies of these arrays
	double **shift2;
	double **shift3;
	double **shift4;
	double **shift5;
	double **shift6;
	double *accumulator2;
	double *accumulator3;
	double *accumulator4;
	double *accumulator5;
	double *accumulator6;

public:

	CrossVectorCorrelator () {numcorrelators=0;} ;
	CrossVectorCorrelator (const unsigned int numcorrin, const unsigned int pin, const unsigned int min);
	~CrossVectorCorrelator();

	void setsize (const unsigned int numcorrin = 32, const unsigned int pin = 16, const unsigned int min = 2);

	void add(const double wA0, const double wA1, const double wA2, 
		const double wB0, const double wB1, const double wB2, const unsigned int k = 0);

	void initialize();
	void clear();

	void save(FILE *f);
	void read(FILE *f);
	};

//////////////////////////////////////////////////////////////////////////////////
/// Class for Mean Square displacement (diffusion, modified from VectorCorrelator)
class DiffusionCorrelator : public VectorCorrelator {

public:

	DiffusionCorrelator () {numcorrelators=0;} ;
	DiffusionCorrelator (const unsigned int numcorrin, const unsigned int pin, const unsigned int min);
	~DiffusionCorrelator() {};

	void add(const double w0, const double w1, const double w2, const unsigned int k = 0);

	// evaluate needs to be rewritten in order to correct for the diffusion problem
        // NO CORRECTION IS NEEDED NOW
	// void evaluate();
	};

//////////////////////////////////////////////////////////////////////////////////
/// Class for <R4> (fourth moment of the displacement)  (diffusion, modified from VectorCorrelator)
class R4Correlator : public VectorCorrelator {

public:

	R4Correlator () {numcorrelators=0;} ;
	R4Correlator (const unsigned int numcorrin, const unsigned int pin, const unsigned int min);
	~R4Correlator() {};

	void add(const double w0, const double w1, const double w2, const unsigned int k = 0);

	};


//////////////////////////////////////////////////////////////////////
// Class for Anisotropic mean square displacement
class AnisotropicDiffusionCorrelator : public VectorCorrelator {
   protected:
      double **correlation2;
      double **shift4;
      double **shift5;
      double **shift6;

   public:
      double *f2;

      AnisotropicDiffusionCorrelator() {numcorrelators=0;} ;
      AnisotropicDiffusionCorrelator (const unsigned int numcorrin, const unsigned int pin, const unsigned int min);
      ~AnisotropicDiffusionCorrelator();

      void setsize (const unsigned int numcorrin = 32, const unsigned int pin = 16, const unsigned int min = 2);


      double calcparcorr(const double r0x, const double r0y, const double r0z, 
            const double ux, const double uy, const double uz, 
            const double r1x, const double r1y, const double r1z);

      double calcpercorr(const double r0x, const double r0y, const double r0z,
            const double ux, const double uy, const double uz,
            const double r1x, const double r1y, const double r1z);


      void add(const double w0, const double w1, const double w2, const double u0, const double u1, const double u2, const unsigned int k = 0);

      // EVALUATE IS NEW
      void evaluate();
      double getf2(int i) {return f2[i];}

};


//////////////////////////////////////////////////////////////////////////////////////////////////////////////////
/// Class for single chain Dynamic structure factor of Gaussian chain, calculated as Correlations 
/// f(tau) = 1/3 <(c0(t)*c0(t+tau> + c1(t)*c1(t+tau) + c2(t)*c2(t+tau) +
///				 (s0(t)*s0(t+tau> + s1(t)*s1(t+tau) + s2(t)*c2(t+tau)>
/// with
///			c_d = sum_{i=nleft}^{nright} cos(qa[q] * r[k][i][d])
///			s_d = sum_{i=nleft}^{nright} sin(qa[q] * r[k][i][d])
/// Derived from CrossVectorCorrelator, which requires the same memory allocation
class SqtCorrelatorGaussianChain : public CrossVectorCorrelator {

   public:

	  SqtCorrelatorGaussianChain () {numcorrelators=0;} ;
	  SqtCorrelatorGaussianChain (const unsigned int numcorrin, const unsigned int pin, const unsigned int min);
      ~SqtCorrelatorGaussianChain() {};

      /** Add scattering data to the correlator 
        Data to be calculated out of this function
        c_d = sum_{i=nleft}^{nright} cos(qa[q] * r[k][i][d]
        s_d = sum_{i=nleft}^{nright} sin(qa[q] * r[k][i][d]
        */
      void add(const double c0, const double c1, const double c2, 
            const double s0, const double s1, const double s2, const unsigned int k = 0);
};

// Dynamic structure factor of a 3D moving point - 1 q value
class SqtCorrelatorIsotropic : public VectorCorrelator {

public:

	SqtCorrelatorIsotropic() { numcorrelators = 0; };
	SqtCorrelatorIsotropic(const unsigned int numcorrin, const unsigned int pin, const unsigned int min);
	~SqtCorrelatorIsotropic() {};

	// Add Rx, Ry and Rz
	void add(const double w0, const double w1, const double w2, const unsigned int k = 0);

	void setQ(const double qin) {
		q = qin;
	};
private:
	double q;
};

// Dynamic structure factor of a 3D moving point - Many q values
class SqtCorrelatorIsotropicManyQ : public VectorCorrelator {

public:

	SqtCorrelatorIsotropicManyQ() { numcorrelators = 0; };
	SqtCorrelatorIsotropicManyQ(const unsigned int numcorrin, const unsigned int pin, const unsigned int min);
	~SqtCorrelatorIsotropicManyQ();

	// Add Rx, Ry and Rz
	void add(const double w0, const double w1, const double w2, const unsigned int k = 0);

	void setQ(const int nqin, const double *qin); 

	void evaluate();
	void toaverage();
	void clear();
	void initialize();

	double **f2, **f2av; // Array for additional results from additional q values
    
    double getf(int i, int j) { 
        if (j==0)
            return f[i];
        else
            return f2[i][j-1]; 
    }

private:
	unsigned int nq;
	double* q;
	double ***correlation2; // Array containing the actual calculated correlation function 
		// Additional space for additional q values
        
};


///////////////////////////////////////////////////////////////////////////////////////////////////////////
// Class for correlation functions that need all the coordinates of a chain 
// Not derived from any other class, just inspired in the bare correlator class
// It calculates N different results
// In this example template, we calculate the mean-square displacement of chain monomers
///////////////////////////////////////////////////////////////////////////////////////////////////////////
class ChainCorrelator {

protected:
	
	double ***shift; // Where the coming values are stored 
	double ***correlation; // Array containing the actual calculated correlation function 
	unsigned long int **ncorrelation; // Number of values accumulated in cor 
	
	double **accumulator; // Accumulator in each correlator 
	unsigned int *naccumulator; // Index that controls accumulation in each correlator 
	unsigned int *insertindex; // Index pointing at the position at which the current value is inserted 
	unsigned int numcorrelators; // Number of Correlators 
	
	unsigned int p; // Points per correlator
	unsigned int m; // Number of points over which to average; RECOMMENDED: p mod m = 0
	unsigned int dmin; // Minimum distance between points for correlators k>0; dmin = p/m 
	unsigned int length; // Lenght of result arrays
	unsigned int kmax; // Maximum correlator attained during simulation
	unsigned int nresults; // Number of correlation results to calculate
	double *params; // Parameter that describes each one of the results (double, but can be cast into an integer)
	unsigned int nmon; // Number of monomers perchain
	unsigned int dim; // Dimension (2 or 3)
	unsigned int arraysize; // Size of array

public:
	double *t, **f, *tav, **fav;
	unsigned int npcorr, npcorrmax, nexp;

	ChainCorrelator() { numcorrelators = 0; }; 
	ChainCorrelator(const unsigned int numcorrin, const unsigned int pin, const unsigned int min, const unsigned int nresultsin, const unsigned int nmonin, const unsigned int dimin = 3);
	~ChainCorrelator();

	void setsize(const unsigned int numcorrin = 32, const unsigned int pin = 16, const unsigned int min = 2, const unsigned int nresultsin = 1, const unsigned int nmonin = 20, const unsigned int dimin = 3);
	void setparameters(const double *paramsin);
	void add(const double *w, const unsigned int k = 0);
	void evaluate();
	void initialize();
	void toaverage();
	void clear();

	// Return t and f
	double gett(int i) { return t[i]; }
	double getf(int i, int j) { return f[i][j]; }

};


class SqtChainCorrelator : public ChainCorrelator {

public:
	SqtChainCorrelator() { numcorrelators = 0; };
	SqtChainCorrelator(const unsigned int numcorrin, const unsigned int pin, const unsigned int min, const unsigned int nresultsin, const unsigned int nmonin, const unsigned int dimin = 3);
	~SqtChainCorrelator() {};

	void add(const double *w, const unsigned int k = 0);
};

// Class to calculate the full probability distribution of displacements for a group of particles
// (they may belong to the same molecule or not)
// nresults means the number of bins per correlator
// Parameters set the max displacement to be considered for each correlator level
// It only calculates the X component of the PDF
class PDFDisplacementCorrelator : public ChainCorrelator {

public:
	double *dmax;

	PDFDisplacementCorrelator() { numcorrelators = 0; };
	PDFDisplacementCorrelator(const unsigned int numcorrin, const unsigned int pin, const unsigned int min, const unsigned int nresultsin, const unsigned int nmonin, const unsigned int dimin = 3);
	void setsize(const unsigned int numcorrin = 32, const unsigned int pin = 16, const unsigned int min = 2, const unsigned int nresultsin = 1, const unsigned int nmonin = 20, const unsigned int dimin = 3);
	~PDFDisplacementCorrelator() {};

	void add(const double *w, const unsigned int k = 0);
	void evaluate();
	double getdmax(int i) { return dmax[i]; }
};

// Class to calculate the non-Gaussian parameter for a distribution of displacements for a group of particles
// (they may belong to the same molecule or not)
// nresults must be equal to 3 (<r2>, <r4> and <ngp>)
class NGPDisplacementCorrelator : public ChainCorrelator {

public:
	NGPDisplacementCorrelator() { numcorrelators = 0; };
	NGPDisplacementCorrelator(const unsigned int numcorrin, const unsigned int pin, const unsigned int min, const unsigned int nresultsin, const unsigned int nmonin, const unsigned int dimin = 3);
	void setsize(const unsigned int numcorrin = 32, const unsigned int pin = 16, const unsigned int min = 3, const unsigned int nresultsin = 1, const unsigned int nmonin = 20, const unsigned int dimin = 3);
	~NGPDisplacementCorrelator() {};

	void add(const double *w, const unsigned int k = 0);
	void evaluate();
};


// Class to calculate Chi_4 
class Chi4Correlator : public ChainCorrelator {
public:
	double a, asq;
	double Lx, Ly, Lz;
	double Lxinv, Lyinv, Lzinv;

	Chi4Correlator() { numcorrelators = 0;};
	Chi4Correlator(const unsigned int numcorrin, const unsigned int pin, const unsigned int min, const unsigned int nresultsin, const unsigned int nmonin, const unsigned int dimin = 3);
	void setsize(const unsigned int numcorrin = 32, const unsigned int pin = 16, const unsigned int min = 2, const unsigned int nresultsin = 1, const unsigned int nmonin = 20, const unsigned int dimin = 3);
	~Chi4Correlator() {};

	void add(const double *w, const unsigned int k = 0);
	void evaluate();
	void seta(double ain) {a = ain; asq=a*a;}
	void setL(double Lxin, double Lyin, double Lzin) {Lx=Lxin; Ly=Lyin; Lz=Lzin; Lxinv=1.0/Lx; Lyinv=1.0/Ly; Lzinv=1.0/Lz;}
	double geta() {return a;}

};

#endif
