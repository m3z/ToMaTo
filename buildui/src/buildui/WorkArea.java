package buildui;
/*
 * Copyright (c) 2002-2006 University of Utah and the Flux Group.
 * All rights reserved.
 * This file is part of the Emulab network testbed software.
 * 
 * Emulab is free software, also known as "open source;" you can
 * redistribute it and/or modify it under the terms of the GNU Affero
 * General Public License as published by the Free Software Foundation,
 * either version 3 of the License, or (at your option) any later version.
 * 
 * Emulab is distributed in the hope that it will be useful, but WITHOUT ANY
 * WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
 * FOR A PARTICULAR PURPOSE.  See the GNU Affero General Public License for
 * more details, which can be found in the file AGPL-COPYING at the root of
 * the source tree.
 * 
 * You should have received a copy of the GNU Affero General Public License
 * along with this program.  If not, see <http://www.gnu.org/licenses/>.
 */

import java.awt.*;
import java.util.*;
import java.lang.*;

import buildui.connectors.EmulatedConnection;
import buildui.connectors.InternetConnector;
import buildui.connectors.Connection;
import buildui.connectors.Connector;
import buildui.devices.Device;
import buildui.devices.Interface;
import buildui.devices.KvmDevice;
import buildui.paint.NetElement;
import java.util.logging.Level;
import java.util.logging.Logger;
import javax.xml.parsers.DocumentBuilder;
import javax.xml.parsers.DocumentBuilderFactory;
import javax.xml.parsers.ParserConfigurationException;
import org.w3c.dom.Document;
import org.w3c.dom.Element;

// Code for the "workarea" of the applet,
// which contains the node graph.
// Contains code to add/remove/select/draw "Thingees".
//
// A lot of this code deals with loading and saving the
// work area as NS, and could probably be in a separate class.
//
public class WorkArea {

  private Vector<NetElement> elements;
  private Vector<Connection> connectionElements;
  private Vector<Interface> interfaceElements;

  public WorkArea (int w, int h) {
    super();
    elements = new Vector();
    connectionElements = new Vector();
    interfaceElements = new Vector();
  }

  private void selectOneInRectangle (Rectangle r, NetElement t, boolean xor) {
    int xDiff = t.getX() - r.x;
    int yDiff = t.getY() - r.y;
    if (xDiff > 0 && xDiff < r.width && yDiff > 0 && yDiff < r.height)
      if (!xor || !t.isSelected())
        t.select();
      else
        t.deselect();
  }

  public void selectRectangle (Rectangle r, boolean xor) {
    Enumeration linkThingeeEnum = connectionElements.elements();

    while (linkThingeeEnum.hasMoreElements()) {
      NetElement t = (NetElement)linkThingeeEnum.nextElement();
      selectOneInRectangle(r, t, xor);
    }

    Enumeration thingeeEnum = elements.elements();

    while (thingeeEnum.hasMoreElements()) {
      NetElement t = (NetElement)thingeeEnum.nextElement();
      selectOneInRectangle(r, t, xor);
    }

    Enumeration iFaceThingeeEnum = interfaceElements.elements();

    while (iFaceThingeeEnum.hasMoreElements()) {
      NetElement t = (NetElement)iFaceThingeeEnum.nextElement();
      selectOneInRectangle(r, t, xor);
    }
  }

  public int getElementCount () {
    return connectionElements.size() + elements.size() + interfaceElements.size();
  }

  public void paint (Graphics g) {
    Enumeration linkThingeeEnum = connectionElements.elements();

    while (linkThingeeEnum.hasMoreElements()) {
      NetElement t = (NetElement)linkThingeeEnum.nextElement();
      t.draw(g);
    }

    Enumeration thingeeEnum = elements.elements();

    while (thingeeEnum.hasMoreElements()) {
      NetElement t = (NetElement)thingeeEnum.nextElement();
      t.draw(g);
    }

    Enumeration iFaceThingeeEnum = interfaceElements.elements();

    while (iFaceThingeeEnum.hasMoreElements()) {
      NetElement t = (NetElement)iFaceThingeeEnum.nextElement();
      t.draw(g);
    }
  }

  public NetElement clicked (int x, int y) {
    Enumeration thingeeEnum;

    NetElement got = null;

    thingeeEnum = connectionElements.elements();

    while (thingeeEnum.hasMoreElements()) {
      NetElement t = (NetElement)thingeeEnum.nextElement();
      if (t.clicked(x, y)) got = t;
    }

    thingeeEnum = elements.elements();

    while (thingeeEnum.hasMoreElements()) {
      NetElement t = (NetElement)thingeeEnum.nextElement();
      if (t.clicked(x, y)) got = t;
    }

    thingeeEnum = interfaceElements.elements();

    while (thingeeEnum.hasMoreElements()) {
      NetElement t = (NetElement)thingeeEnum.nextElement();
      if (t.clicked(x, y)) got = t;
    }

    return got;
  }

  public void remove (NetElement t) {
    if (t instanceof Interface)
      interfaceElements.removeElement(t);
    else if (t instanceof Connection) {
      boolean done = false;
      while (!done) {
        done = true;
        Enumeration e = interfaceElements.elements();
        while (e.hasMoreElements() && done) {
          Interface i = (Interface)e.nextElement();
          if (i.isConnectedTo(t)) {
            remove(i);
            done = false;
          }
        }
      }
      connectionElements.removeElement(t);
    } else {
      boolean done = false; // stupid hack.
      while (!done) {
        done = true;
        Enumeration thingeeEnum = connectionElements.elements();
        while (thingeeEnum.hasMoreElements() && done) {
          Connection u = (Connection)thingeeEnum.nextElement();
          if (u.isConnectedTo(t)) {
            remove(u);
            done = false;
          }
        }
      }
      elements.removeElement(t);
    }
  }

  public void add (NetElement t) {
    if (t instanceof Connection)
      connectionElements.addElement((Connection)t);
    else if (t instanceof Interface)
      interfaceElements.addElement((Interface)t);
    else
      elements.addElement(t);
  }

  public Document encode (boolean modify) {
    try {
      DocumentBuilderFactory dbfac = DocumentBuilderFactory.newInstance();
      DocumentBuilder docBuilder = dbfac.newDocumentBuilder();
      Document doc = docBuilder.newDocument();
      Element root = doc.createElement("topology");
      doc.appendChild(root);
      Element devices = doc.createElement("devices");
      root.appendChild(devices);
      Element connectors = doc.createElement("connectors");
      root.appendChild(connectors);
      for ( NetElement el: elements) {
        if ( el instanceof Device ) {
          Element x_dev = doc.createElement("device") ;
          ((Device)el).writeAttributes(x_dev);
          for ( Interface iface: interfaceElements ) {
            if ( iface.getDevice() == el ) {
              Element x_iface = doc.createElement("interface") ;
              iface.writeAttributes(x_iface);
              x_dev.appendChild(x_iface);
            }
          }
          devices.appendChild(x_dev);
        } else if ( el instanceof Connector ) {
          Element x_con = doc.createElement("connector") ;
          ((Connector)el).writeAttributes(x_con);
          for ( Connection con: connectionElements ) {
            if ( con.getConnector() == el ) {
              Element x_c = doc.createElement("connection") ;
              con.writeAttributes(x_c);
              for ( Interface iface: interfaceElements ) {
                if ( iface.getConnection() == con ) {
                  x_c.setAttribute("device", iface.getDevice().getName());
                  x_c.setAttribute("interface", iface.getName());
                  break;
                }
              }
              x_con.appendChild(x_c);
            }
          }
          connectors.appendChild(x_con);
        }
      }
      return doc ;
    } catch (ParserConfigurationException ex) {
      Logger.getLogger(Netbuild.class.getName()).log(Level.SEVERE, null, ex);
      return null ;
    }
  }

}