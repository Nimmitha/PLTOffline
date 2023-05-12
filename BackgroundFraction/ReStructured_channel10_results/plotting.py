import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

import ROOT
from ROOT import RooFit, TCanvas

IMG_PATH = "plots/"


def plot_box(model, frame1, chi2, ntracks_time, t1_string, t2_string, h, Fill):
    fFile_box = IMG_PATH + "fit_slopeY" + Fill + "_" + str(h) + "_box.png"
    # startTime new canvas (box)
    c_box = TCanvas("c_box", "c_box", 800, 700)
    c_box.GetPad(0).SetLogy()
    frame1.SetMaximum(1e6)
    frame1.SetMinimum(0.2)
    frame1.GetYaxis().SetTitleOffset(1.2)
    frame1.GetYaxis().SetTitleSize(0.04)

    rh = frame1.findObject("dataSet")
    N = rh.GetN()
    for i in range(N):
        x = rh.GetPointX(i)
        y = rh.GetPointY(i)
        if y == 0.0:
            rh.SetPointError(i, 0., 0., 0., 0.)

    # ParamBox
    model.paramOn(frame1, RooFit.Layout(0.7), RooFit.Format(("NEU"), RooFit.AutoPrecision(1)))
    frame1.getAttText().SetTextSize(0.02)
    pt = frame1.findObject("model_paramBox")
    pt.AddText(ROOT.Form(f"Chi2/ndof =  {chi2:.2f}"))
    pt.AddText(ROOT.Form(f"Tracks =  {ntracks_time}"))

    pt.AddText(f'timesec = {t1_string} - {t2_string}')
    frame1.Draw()
    c_box.SaveAs(fFile_box)
    # frame1.Clear()
    # c_box.Clear()
    del c_box
    del frame1


def plot_table(df, h):
    with PdfPages(f"{IMG_PATH+str(h)}_plots.pdf") as pdf:
        for col in df.columns:
            # print(col)
            plt.figure()
            plt.hist(df[col], bins=50, ls='solid', linewidth=3, edgecolor='k', alpha=.5, color='b')

            plt.title(col)
            plt.xlabel(col)
            plt.ylabel("No. of tracks")
            plt.yscale('log')
            # plt.ylim([0, y_max*1.15])
            plt.grid()

            # y_max = max( max(outX[0]), max(outY[0]) )
            mean = df[col].mean()
            std = df[col].std()
            nfits = df.shape[0]

            textstr = f"{nfits:} fits\nMean: {mean:.2f}\nStd: {std:.2f}\n"
            plt.text(0.6, 0.8, textstr, transform=plt.gca().transAxes,
                     fontsize=24, verticalalignment='top', horizontalalignment='left',
                     bbox=dict(facecolor='white', alpha=0.5, edgecolor='none'))
            # hep.cms.label("Work in Progress", data=True, loc=1)
            # plt.savefig(f"{IMG_PATH+str(h)}_{col}.png")

            pdf.savefig()
            plt.close()
