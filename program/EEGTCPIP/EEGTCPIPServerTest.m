clc;
clear;
close all;

ipAddress = 'localhost';
Port = 8888;
nChan = 9;
sampleRate = 1000;
bufferSize = 4;
updateInterval = 0.04;

% calculate update points
if round(sampleRate * updateInterval) > 1
    updatePoints = round(sampleRate * updateInterval);
else
    updatePoints = sampleRate;
end

dataServer = tcpserver(ipAddress,Port);
dataServer.OutputBufferSize = 4*nChan*updatePoints*10;

x=0;
rst = [];
diffx = [];

fopen(dataServer);

tic;
while ~KbCheck
    if length(rst)>=nChan*updatePoints
        fwrite(dataServer,rst,'float');
        rst = [];
    end
    for i=0:7
        rst=[rst sin(x+i*pi/2)];
    end
    if toc>=1
        rst = [rst x];
        diffx = [diffx x];
        tic;
    else
        rst = [rst 0];
    end
    x=x+1;
end

fclose(dataServer);	