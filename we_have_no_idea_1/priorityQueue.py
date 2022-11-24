class MinPriorityQueue:
  """ Priority Queue implementation
  We use a list to store a tuple of element with its priority
  However, the first element to dequeue is the one with the minimum priority
  """


  def __init__(self):
      self.queue = []
      self.length = 0
  
  
  def enqueue(self, element, priority):
    """
    Enqueue a new element into the queue along with it's priority,
    Sort the queue in ascending order of priority
    """
    self.queue.append((element, priority))
    self.length += 1

  
  def isEmpty(self):
    """
    Check whether the queue is empty
    """
    return self.length == 0

  def dequeue(self):
    """
    Get the first element which has the minimum priority, remove it from the queue
    And return the element for further purposes
    """
    self.queue.sort(key = lambda x: x[1])
    self.length -= 1
    return self.queue.pop(0)[0]

  def changePriority(self, element, newPriority):
    """
    Change the priority of an element in the queue
    Sort the queue in order of ascending priority after the change
    """
    for i in range(len(self.queue)):
      if self.queue[i][0] == element:
        self.queue[i] = (element, newPriority)