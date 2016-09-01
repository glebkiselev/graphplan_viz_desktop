import copy
from graph_tool.centrality import betweenness
from graph_tool.draw import GraphWindow, prop_to_size, sfdp_layout
from graph_tool import *
import time
import logging


from gi.repository import Gtk, Gdk, GdkPixbuf, GObject

sol_nodes = []
edge_list = []
vlist = []


diameter = 15

gr = Graph()

vp, ep = betweenness(gr)

GRAY = [0.5, 0.5, 0.5, 0.5]
BLUE = [0, 0.5, 0.8, 1]
RED = [0.9, 0, 0.2, 1]
YELLOW = [1, 1, 0.1, 1]

e_color = gr.new_edge_property("vector<double>")
v_color = gr.new_vertex_property("vector<double>")
# vert search property
vprop = gr.new_vertex_property("string")
# names of edges
edge_name = gr.new_edge_property("string")
# vertice names
vertex_name = gr.new_vertex_property("string")

# edges names
gr.edge_properties["name"] = edge_name
#vertex names
gr.vertex_properties["name"] = vertex_name
v_to_step_back = []
e_to_step_back = []


def uniq_nodes(list_nodes):
    # nodes vs only uniq state
    uniq = []
    set_of_states = set()
    for node in list_nodes:
        if node.state not in set_of_states:
            uniq.append(node)
            set_of_states.add(node.state)


    logging.info("len of  list_nodes: {0} , len of uniq set: {1}".format(len(list_nodes), len(uniq)))

    return copy.deepcopy(uniq)

def make_sol_nodes(pop_node, list_nodes):
    while pop_node.parent is not None:
        sol_nodes.append(pop_node)
        pop_node = pop_node.parent
    # finding the sol_nodes in existing nodes
    sol2_nodes = sol_nodes.copy()
    for node in list_nodes:
        for i, sol2_node in enumerate(sol2_nodes):
            if sol2_node.state == node.state:
                sol_nodes[i] = node
    return sol_nodes

def mark_sol_vertice(vlist, sol_nodes, list_nodes, vprop):
    # Marking vertice that are equal states of sol_node
    v_sol_list = []
    for sol_node in sol_nodes:
        for v in vlist:
            if vprop[v] == str(sol_node.state):
                v_sol_list.append(v)
    for v in vlist:
        for node in [node for node in list_nodes if node.g == 0]:
            if vprop[v] == str(node.state):
                v_sol_list.append(v)
    return v_sol_list[::-1]

def mark_sol_edges(v_sol_list, gr):
    # creating a list of edges for solution
    for v1 in v_sol_list:
        for v2 in v_sol_list:
            if gr.edge(v1, v2):
                edge_list.append(gr.edge(v1, v2))
    return edge_list

def graph_creater(list_nodes):
    # vertices creation
    for node in list_nodes:
        v = gr.add_vertex()
        v_color[v] = GRAY
        vprop[v] = str(node.state)
        vlist.append(v)
    # edges creation
    for node in list_nodes:
        if node.parent:
            # target all other nodes
            for other_node in [x for x in list_nodes if x != node]:
                # searching for node.state == parent.state
                if node.parent.state == other_node.state:
                    # making edge from parent to target
                    for v in vlist:
                        if vprop[v] == str(node.parent.state):
                            start = v
                        if vprop[v] == str(node.state):
                            target = v
                    ed = gr.add_edge(start, target)
                    e_color[ed] = GRAY
                    if node.action:
                        edge_name[ed] = str(node.action.name)
    return vlist

def visualizer():
    pos = sfdp_layout(gr)
    win = GraphWindow(gr, pos, geometry=(1000, 700),
                      edge_color=e_color,
                      vertex_size=prop_to_size(vp, mi=diameter, ma=diameter),
                      edge_pen_width=prop_to_size(ep, mi=3, ma=3),
                      edge_text=gr.edge_properties["name"],
                      vertex_text = gr.vertex_properties["name"],
                      vertex_fill_color=v_color,
                      vertex_halo_color=[0.8, 0, 0, 0.6])
    return win

# vertice info
def in_vertice(win):
    # try with picked:
    if (win.graph.picked is not None and win.graph.picked is not False):
        return (vprop[win.graph.picked])

# callback with Gtk.Menu - call in the place of pointer
def button_clicked(widget, event):
    menu = Gtk.Menu()
    item = Gtk.MenuItem(in_vertice(widget)[11:-2])
    menu.append(item)
    menu.show_all()
    menu.popup(None, None, None, None, event.button, event.time)

    return True

def graphplan(list_nodes, pop_node):

    list_nodes = uniq_nodes(list_nodes)

    vlist = graph_creater(list_nodes)

    sol_nodes = make_sol_nodes(pop_node, list_nodes)

    v_sol_list = mark_sol_vertice(vlist, sol_nodes, list_nodes, vprop)

    edge_list = mark_sol_edges(v_sol_list, gr)

    length_of_solution = len(v_sol_list)

    win = visualizer()

    def key_press_event(widget, event):
        if event.keyval == 65363:
            update_state()
        if event.keyval == 65361:
            step_back()

    def update_state():
        if len(v_sol_list) == length_of_solution:
            v_color[v_sol_list[0]] = YELLOW
            vertex_name[v_sol_list[0]] = "start"
            v_to_step_back.append(v_sol_list[0])
            v_sol_list.remove(v_sol_list[0])
        elif len(v_sol_list) == 1:
            v_color[v_sol_list[0]] = YELLOW
            vertex_name[v_sol_list[0]] = "end"
            v_to_step_back.append(v_sol_list[0])
            v_sol_list.remove(v_sol_list[0])
        elif len(v_sol_list):
            v_color[v_sol_list[0]] = BLUE
            v_to_step_back.append(v_sol_list[0])
            v_sol_list.remove(v_sol_list[0])

        if len(edge_list):
            e_color[edge_list[0]] = RED
            e_to_step_back.append(edge_list[0])
            edge_list.remove(edge_list[0])
        #time.sleep(1)
        win.graph.regenerate_surface()
        win.graph.queue_draw()
        return True

    def step_back():
        if v_to_step_back:
            last_v = v_to_step_back.pop()
            if v_color[last_v] == YELLOW or BLUE:
                v_color[last_v] = GRAY
                vertex_name[last_v] = ''
                v_sol_list.insert(0, last_v)
        if e_to_step_back:
            last_e = e_to_step_back.pop()
            if e_color[last_e] == RED:
                e_color[last_e] = GRAY
                edge_list.insert(0, last_e)
        win.graph.regenerate_surface()
        win.graph.queue_draw()
        return True


    #win.connect('button-press-event', butPress)
    win.connect('button-press-event', button_clicked)
    win.connect('key-press-event', key_press_event)

    # We will give the user the ability to stop the program by closing the window.
    win.connect("delete_event", Gtk.main_quit)


    win.show_all()
    Gtk.main()