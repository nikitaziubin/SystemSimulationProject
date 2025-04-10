import simpy
from simpy_helpers import Entity, Resource, Source, Stats
import numpy as np 
import matplotlib.pyplot as plt 
import seaborn as sns 

NUM_ENTITIES = 200
MEAN_TIME_BETWEEN_ARRIVALS = 50
MEAN_SERVICE_TIME = 30

# how an entity proceeds through the simulation
class processEntity(Entity):
    
    def process(self):
        # first, wait for space to open up at a resource
        yield self.wait_for_resource(my_resource)
        # then, process at the resource
        # we'll define the resource in the next step
        yield self.process_at_resource(my_resource)

        # leave the resource and open up a spot for the next entity
        self.release_resource(my_resource)
        
        # once process ends, the entity leaves the simulation

class myResource(Resource):
    def service_time(self, entity):
        # we could define this as a fixed or stochastic time
        # when using stochastic, it's often modeled as a draw from an exponential distro
        return np.random.exponential(MEAN_SERVICE_TIME) 


class generateCustomers(Source):
    
    def interarrival_time(self):
        # interarrival time: time between each entity arriving in the simulation
        # also modeled as a draw from an exponential 
        return np.random.exponential(MEAN_TIME_BETWEEN_ARRIVALS)
    
    def build_entity(self):
        # set the attributes of each entity entering the simulation 
        attributes = {}
        attributes['customer'] = np.random.choice(['standard', 'priority'])
        if attributes['customer'] == 'priority':
            attributes['priority'] = 0 
        
        # remember we defined the processEntity class in step 1
        return processEntity(env, attributes) 

# setting a random seed will ensure that our pseudo-randomness is replicable 
np.random.seed(34) 

# the environment that will run the whole simulation
env = simpy.Environment()

# create a resource object and set its capacity 
# recall that myResource inherits from the Resource class from simpy_helpers
# capacity is the number of entities that can receive service simultaneously before a queue forms
# here we're modeling an M/M/1 queue 
my_resource = myResource(env, capacity=1) 

# specify the number of jobs 
my_source = generateCustomers(env, number=NUM_ENTITIES) 

# kick off the simulation with the source class that generates jobs/customers 
env.process(my_source.start(debug=False)) # Set debug to false to suppress lots of output

#  Run the simulation! 
env.run() 


Stats.get_total_times()[:5]
print(f"Customer average time in simulation = {np.mean(Stats.get_total_times()):0.5} ")
print(f"Customer average time waiting = {np.mean(Stats.get_waiting_times()):0.5} ")
print(f"Customer average time processing = {np.mean(Stats.get_processing_times()):0.5} ")
print("       ==================      ")
print(f"Customer average time waiting (standard) = {np.mean(Stats.get_waiting_times(my_resource, attributes={'customer': 'standard'})):0.6} ")
print(f"Customer average time waiting (priority) = {np.mean(Stats.get_waiting_times(my_resource, attributes={'customer': 'priority'})):0.5} ")
print(f"Resource average processing time = {np.mean(Stats.get_processing_times(my_resource)):0.5} ")

system_times = Stats.get_total_times()

sns.histplot(system_times,bins=7)
plt.xlabel('Time in simulation')
plt.show()

resource_queue = Stats.queue_size_over_time(my_resource)
sns.lineplot(y=resource_queue,x=range(0,len(resource_queue)))
plt.ylabel('Queue size')
plt.xlabel('Queue size over time')
plt.show()