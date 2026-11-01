There's something to adjust in /work/w04: Individualize drawing attributes

A set of improvements to the existing visualization suite aimed to align the current functionality with what will be implemented after the refactor. 

Some attributes can only have one value per visualization, such as node font color or arrow style for directed graphs, but if attributes are read from the graph, we should allow individual values for all of these. 

While I haven't broken any of the existing tests, I'm not sure that I fully understand the testing infrastructure for the visualization module. Tests will need to be added, but I'm still working on it. 

Below are some examples on the karate club graph. 
```python
nx.draw_networkx(G, pos=pos, ax=ax, node_shape='o', 
    font_size={n: int(n / (34/15) + 5) for n in G.nodes()}, 
    font_color={n: 'k' if n % 2 == 0 else 'r' for n in G.nodes()})
```
![image](https://github.com/user-attachments/assets/40c60c45-3f53-4f49-a163-5d7991d9a1f6)
```python
nx.draw_networkx(G, ax=plt.axes(), 
    node_shape=np.array(['o' if n % 2 == 0 else '^' for n in G.nodes()]))
```
![image](https://github.com/user-attachments/assets/361404db-e822-44ed-a774-7bc50a9990ed)
```python
arrowstyles = ["-|>" if (u + v) % 2 == 0 else "-[" for u, v in G.edges()]
arrowsizes = [(u+v)/2 for u, v in G.edges()]
nx.draw_networkx(G, ax=plt.axes(), arrows=True, arrowstyle=arrowstyles, arrowsize=arrowsizes)
```
![image](https://github.com/user-attachments/assets/a90d2b29-ca74-43c6-8e2e-6c7f5164013b)
```python
min_source_margin = [u for u, _ in G.edges()]
min_target_margin = [v for _, v in G.edges()]
nx.draw_networkx(G, ax=plt.axes(), arrows=True, min_source_margin=min_source_margin, min_target_margin=min_target_margin)
```
![image](https://github.com/user-attachments/assets/0d0e636d-2e19-4900-856a-9b6bf8ba9119)

Individualize drawing attributes A set of improvements to the existing visualization suite aimed to align the current functionality with what will be implemented after the refactor. Some attributes can only have one value per visualization, such as node font color or arrow style for directed graphs, but if attributes are read from the graph, we should allow individual values for all of these. While I haven't broken any of the existing tests, I'm not sure that I fully understand the testing infrastructure for the visualization module. Tests will need to be added, but I'm still working on it. Below are some examples on the karate club graph. ![image]( ![image]( ![image]( ![image](

So I've added some basic tests, but some of the tests in `test_pylab` don't seem to have any assertions (like the `test_labels_and_colors` test. Since there is not decorator, I think this is just checking that no exceptions are raised in the calls to `draw_networkx_*`. It is also the only test that references any font-specific attribute (in this case font size). Do we need to add more tests for things like font weight, font color, etc? I've added a call using multiple font colors.