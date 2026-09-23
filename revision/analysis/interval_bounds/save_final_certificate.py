"""Re-evaluate final saved refinement supports and persist an auditable dual."""
import numpy as np
from run_interval_bounds import INPUT, OUT, BL, BH, supports, inverse_increments, solve_endpoint, save

if __name__=='__main__':
    step=900;a=np.load(INPUT,mmap_mode='r');n=len(a)//step
    knots=np.tile(np.r_[BL,BH,np.linspace(BL,BH,17)[1:-1]],(n,1))
    for previous in range(3):
        states=np.load(OUT/f'upper_900s_round{previous}.npz')['states']
        knots=np.c_[knots,inverse_increments(a,np.diff(states),step)]
    fs,cs=supports(a,knots,step)
    report,states,b=solve_endpoint(fs,cs,knots,step=step,
        certificate_path=OUT/'upper_900s_round3_dual_certificate.npz')
    report.update(adaptive_round=3,certificate_purpose='Persist dual multipliers, supports and box bounds for independent reconstruction')
    np.savez_compressed(OUT/'upper_900s_round3_certified_solution.npz',states=states,baseline=b)
    save('upper_900s_round3_certificate.json',report)
