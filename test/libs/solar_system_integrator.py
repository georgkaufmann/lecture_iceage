import math

import numpy as np
import random

class PlanetPosVel:

    def __init__(self, x, y, vx, vy):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy


class _PlanetHistory:

    def __init__(self, num_steps):
        self.t = np.zeros(num_steps, np.float64)
        self.x = np.zeros(num_steps, np.float64)
        self.y = np.zeros(num_steps, np.float64)
        self.vx = np.zeros(num_steps, np.float64)
        self.vy = np.zeros(num_steps, np.float64)


class SolarSystem(object):
    """
    Integrate a solar system with the Sun at the center and an
    arbitrary number of planets---we don't model the planet-planet
    interactions.
    We take the Sun to be at the center, and we register planets
    with their semi-major axis, eccentricity, and starting location 
    -- either aphelion or perihelion.
    All orbits are counter-clockwise
    Finally, we don't allow for the ellipses to be rotated -- they
    will all have their semi-major axes aligned with the x-axis.
    We work in units of AU, yr, and M_sun
    In these units, G = 4 pi^2
    Note, we can override these defaults by explicitly setting GM and
    year in the initialization and then passing in a in whatever units
    are desired.
    """

    def __init__(self, GM=4.0*math.pi**2, year=1.0):

        self.GM = GM
        self.year = year

        self.num_planets = 0

        self.a = []
        self.e = []
        self.pos0 = []
        self.rot = []    # rotation of the semi-major axis
        
        
    def add_planet_by_period(self, P, e, loc="perihelion", pos_vel=None):

        a = (self.GM*P**2/(4*math.pi**2))**(1./3.)
        self.add_planet(a, e, loc=loc, pos_vel=pos_vel)
        
        
    def add_planet(self, a, e, loc="perihelion", pos_vel=None, rot=0.0):

        self.num_planets += 1

        self.a.append(a)
        self.e.append(e)
        
        if loc == "perihelion":
            x0 = a*(1.0 - e)
            y0 = 0.0

            vx0 = 0.0
            vy0 = math.sqrt((self.GM/a)*(1.0+e)/(1.0-e))
        
            pos_vel = PlanetPosVel(x0, y0, vx0, vy0)

        elif loc == "aphelion":
            x0 = -a*(1.0 + e)
            y0 = 0.0

            vx0 = 0.0
            vy0 = -math.sqrt((self.GM/a)*(1.0-e)/(1.0+e))

            pos_vel = PlanetPosVel(x0, y0, vx0, vy0)
        
        elif loc == "specify":

            # we should have passed in the position and velocity object
            pass


        self.pos0.append(pos_vel)

        if rot == "random":
            self.rot.append(random.uniform(0.0, 2.0*math.pi))
        else:
            self.rot.append(np.radians(rot))
        

    def period(self, num):
        """
        return the orbital period of planet num
        """

        a = self.a[num]
        return math.sqrt(4*math.pi**2*a**3/(self.GM))


    def integrate(self, nsteps_per_year, num_years):
        """ 
        integrate our system to time num_years (given in years), taking
        nsteps_per_year steps each year.  This does 4th-order Runge-Kutta
        with a fixed timestep.
        """
        
        # we will advance each planet separately
        dt = self.year/nsteps_per_year

        # intermediate results storage
        k1 = np.zeros(4, np.float64)
        k2 = np.zeros(4, np.float64)
        k3 = np.zeros(4, np.float64)
        k4 = np.zeros(4, np.float64)

        Y = np.zeros(4, np.float64)        

        # total number of steps needed
        nsteps = int(num_years*nsteps_per_year)

        # storage for the final solution
        solution = []
        for n in range(self.num_planets):
            solution.append(_PlanetHistory(nsteps+1))
        

        # do the integration -- one planet at a time
        for p in range(self.num_planets):

            Y[:] = np.array([self.pos0[p].x,  self.pos0[p].y,
                             self.pos0[p].vx, self.pos0[p].vy])

            # store the initial conditions
            solution[p].x[0]  = self.pos0[p].x
            solution[p].y[0]  = self.pos0[p].y
            solution[p].vx[0] = self.pos0[p].vx
            solution[p].vy[0] = self.pos0[p].vy

            t = 0
            for n in range(1,nsteps+1):

                f = self.rhs(p, t, Y)
                k1[:] = dt*f[:]

                f = self.rhs(p, t+0.5*dt, Y[:]+0.5*k1[:])
                k2[:] = dt*f[:]

                f = self.rhs(p, t+0.5*dt, Y[:]+0.5*k2[:])
                k3[:] = dt*f[:]

                f = self.rhs(p, t+dt, Y[:]+k3[:])
                k4[:] = dt*f[:]

                Y[:] += (1.0/6.0)*(k1[:] + 2.0*k2[:] + 2.0*k3[:] + k4[:])

                t += dt

                # store this step
                solution[p].t[n] = t
                solution[p].x[n]  = Y[0]
                solution[p].y[n]  = Y[1]
                solution[p].vx[n] = Y[2]
                solution[p].vy[n] = Y[3]


            # do we need to rotate?
            if not self.rot[p] == 0.0:
                oldx = solution[p].x.copy()
                oldy = solution[p].y.copy()

                solution[p].x = oldx*np.cos(self.rot[p]) - oldy*np.sin(self.rot[p])
                solution[p].y = oldy*np.cos(self.rot[p]) + oldx*np.sin(self.rot[p])                

                oldvx = solution[p].vx.copy()
                oldvy = solution[p].vy.copy()

                solution[p].vx = oldvx*np.cos(self.rot[p]) - oldvy*np.sin(self.rot[p])
                solution[p].vy = oldvy*np.cos(self.rot[p]) + oldvx*np.sin(self.rot[p])                
                
                
        return solution

        
    def rhs(self, planet, t, Y):
        """ 
        return the RHS for our system of equations for the planet
        with index planet.  Here Y is [x, y, vx, vy]
        """

        f = np.zeros(4, np.float64)

        # dx/dt = v_x
        f[0] = Y[2]
        
        # dy/dt = v_y
        f[1] = Y[3]

        # d(vx)/dt = -GMx/r**3
        r = np.sqrt(Y[0]**2 + Y[1]**2)
        f[2] = -self.GM*Y[0]/r**3

        # d(vy)/dt = -GMy/r**3
        f[3] = -self.GM*Y[1]/r**3        

        return f
